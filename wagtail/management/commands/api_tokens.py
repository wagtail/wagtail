import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from wagtail.log_actions import log
from wagtail.models import APIToken


class Command(BaseCommand):
    help = "Manage Wagtail API tokens"

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(title="sub-commands", required=True)

        create = subparsers.add_parser("create", help="Create a new API token.")
        create.add_argument(
            "--user",
            required=True,
            help="The user to create the token for (their USERNAME_FIELD value)",
        )
        create.add_argument("--name", required=True, help="A label for the token")
        create.add_argument(
            "--json",
            action="store_true",
            dest="json_output",
            help="Output a JSON object instead of the bare token",
        )
        create.set_defaults(method=self.create)

        list_ = subparsers.add_parser("list", help="List API tokens.")
        list_.add_argument("--user", help="Only show tokens for this user")
        list_.add_argument(
            "--include-revoked",
            action="store_true",
            help="Include revoked tokens",
        )
        list_.set_defaults(method=self.list)

        revoke = subparsers.add_parser("revoke", help="Revoke an API token.")
        revoke.add_argument("--id", type=int, help="Token ID")
        revoke.add_argument("--user", help="Token owner's USERNAME_FIELD value")
        revoke.add_argument("--prefix", help="Token prefix (see list output)")
        revoke.set_defaults(method=self.revoke)

    def handle(self, *args, method, **options):
        method(*args, **options)

    def get_user(self, username):
        User = get_user_model()
        try:
            return User.objects.get(**{User.USERNAME_FIELD: username})
        except User.DoesNotExist:
            raise CommandError(
                f"No user found with {User.USERNAME_FIELD}={username!r}"
            ) from None

    def create(self, *args, user, name, json_output, **options):
        instance, plaintext = APIToken.create_token(user=self.get_user(user), name=name)
        log(instance, "wagtail.apitoken.create", data={"source": "management_command"})
        if json_output:
            self.stdout.write(
                json.dumps(
                    {
                        "token": plaintext,
                        "prefix": instance.prefix,
                        "name": instance.name,
                        "user": instance.user.get_username(),
                        "created": instance.created.isoformat(),
                    }
                )
            )
        else:
            self.stdout.write(plaintext)

    def list(self, *args, user, include_revoked, **options):
        tokens = APIToken.objects.select_related("user").order_by("-created")
        if user:
            tokens = tokens.filter(user=self.get_user(user))
        if not include_revoked:
            tokens = tokens.filter(revoked_at__isnull=True)
        for token in tokens:
            self.stdout.write(
                # The space before the ellipsis keeps it out of copy-pasted prefixes.
                f"{token.pk}\t{token.prefix} …\t{token.name}\t"
                f"{token.user.get_username()}\t{token.created:%Y-%m-%d %H:%M}\t"
                f"last_used={token.last_used_at or 'never'}\t"
                f"revoked={token.revoked_at or 'no'}"
            )

    def revoke(self, *args, id, user, prefix, **options):
        if id is not None:
            matches = APIToken.objects.filter(pk=id, revoked_at__isnull=True)
        elif user and prefix:
            matches = APIToken.objects.filter(
                user=self.get_user(user),
                prefix__startswith=prefix,
                revoked_at__isnull=True,
            )
        else:
            raise CommandError("Provide --id, or --user and --prefix")
        matches = list(matches)
        if not matches:
            raise CommandError(
                "No active token found; it may not exist or may already be revoked."
            )
        if len(matches) > 1:
            raise CommandError(
                f"Expected one active token, found {len(matches)}. "
                "Use a longer --prefix or --id."
            )
        token = matches[0]
        token.revoke()
        log(token, "wagtail.apitoken.revoke", data={"source": "management_command"})
        self.stdout.write(f"Revoked token {token.prefix}… ({token.name})")
