# -*- coding: utf-8 -*-
import requests
import pytz
# import lxml.html
try:
    import xml.etree.cElementTree as ET
except:
    import xmlElementTree as ET
# import lxml.etree
from six.moves import input
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.core.files import File
from django.utils.text import Truncator
from django.utils.html import strip_tags
# from django.contrib.sites.models import Site
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.core.management.base import CommandError
from django.core.management.base import LabelCommand
from django.core.files.temp import NamedTemporaryFile

from wagtail.wagtailcore.models import Page, Site
from wagtail.wagtailimages.models import Image as WagtailImage
from demo.models import StandardPage
# from puput.models import BlogPage, EntryPage, TagEntryPage as PuputTagEntryPage, Tag as PuputTag, \
#     Category as PuputCategory, CategoryEntryPage as PuputCategoryEntryPage

WP_NS = 'http://wordpress.org/export/%s/'


class Command(LabelCommand):
    help = 'Import blog data from Wordpress'
    label = 'WXR file'
    args = 'wordpress.xml'

    # SITE = Site.objects.get_current()

    def add_arguments(self, parser):
        parser.add_argument('--slug', default='blog', help="Slug of the blog.")
        parser.add_argument('--title', default='Blog', help="Title of the blog.")

    def handle_label(self, wxr_file, **options):
        global WP_NS
        self.get_blog_page(options['slug'], options['title'])
        self.tree = ET.parse(wxr_file)
        WP_NS = WP_NS % self.get_wordpress_version(self.tree)
        self.import_authors(self.tree)
        # self.categories = self.import_categories(self.tree.findall(u'channel/{{{0:s}}}category'.format(WP_NS)))
        self.import_entries(self.tree.findall('channel/item'))

    def get_wordpress_version(self, tree):
        """
        Get the wxr version used on the imported wordpress xml.
        """
        for v in ('1.2', '1.1', '1.0'):
            try:
                tree.find(u'channel/{{{0:s}}}wxr_version'.format(WP_NS % v)).text
                return v
            except AttributeError:
                pass
        raise CommandError('Cannot resolve the wordpress namespace')

    def import_authors(self, tree):
        self.stdout.write('Importing authors...')

        post_authors = set()
        for item in tree.findall('channel/item'):
            post_type = item.find(u'{{{0:s}}}post_type'.format(WP_NS)).text
            if post_type == 'post':
                post_authors.add(item.find('{http://purl.org/dc/elements/1.1/}creator').text)

        self.authors = {}
        for post_author in post_authors:
            self.authors[post_author] = self.import_author(post_author.replace(' ', '-'))

    def import_author(self, author_name):
        action_text = u"The author '{0:s}' needs to be migrated to an user:\n" \
                      u"1. Use an existing user ?\n" \
                      u"2. Create a new user ?\n" \
                      u"Please select a choice: ".format(author_name)
        while True:
            selection = str(input(action_text))
            if selection and selection in '12':
                break
        if selection == '1':
            users = User.objects.all()
            if users.count() == 1:
                username = users[0].get_username()
                preselected_user = username
                usernames = [username]
                usernames_display = [u'[{0:s}]'.format(username)]
            else:
                usernames = []
                usernames_display = []
                preselected_user = None
                for user in users:
                    username = user.get_username()
                    if username == author_name:
                        usernames_display.append(u'[{0:s}]'.format(username))
                        preselected_user = username
                    else:
                        usernames_display.append(username)
                    usernames.append(username)
            while True:
                user_text = u"1. Select your user, by typing " \
                            u"one of theses usernames:\n" \
                            u"{0:s} or 'back'\n" \
                            u"Please select a choice: ".format(', '.join(usernames_display))
                user_selected = input(user_text)
                if user_selected in usernames:
                    break
                if user_selected == '' and preselected_user:
                    user_selected = preselected_user
                    break
                if user_selected.strip() == 'back':
                    return self.import_author(author_name)
            return users.get(**{users[0].USERNAME_FIELD: user_selected})
        else:
            create_text = u"2. Please type the email of " \
                          u"the '{0:s}' user or 'back': ".format(author_name)
            author_mail = input(create_text)
            if author_mail.strip() == 'back':
                return self.import_author(author_name)
            try:
                return User.objects.create_user(author_name, author_mail)
            except IntegrityError:
                return User.objects.get(**{User.USERNAME_FIELD: author_name})

    def get_blog_page(self, slug, title):
        # Create blog page
        try:
            self.blogpage = StandardPage.objects.get(slug=slug)
        except StandardPage.DoesNotExist:
            # Get root page
            rootpage = Page.objects.first()

            # Set site root page as root site page
            site = Site.objects.first()
            site.root_page = rootpage
            site.save()

            # Get blogpage content type
            self.blogpage = StandardPage(
                title=title,
                slug=slug,
            )
            rootpage.add_child(instance=self.blogpage)
            revision = self.blogpage.save_revision()
            revision.publish()

    # def import_categories(self, category_nodes):
    #     self.stdout.write('Importing categories...')

    #     categories = {}
    #     for category_node in category_nodes:
    #         title = category_node.find(u'{{{0:s}}}cat_name'.format(WP_NS)).text[:255]
    #         slug = category_node.find(u'{{{0:s}}}category_nicename'.format(WP_NS)).text[:255]
    #         try:
    #             parent = category_node.find(u'{{{0:s}}}category_parent'.format(WP_NS)).text[:255]
    #         except TypeError:
    #             parent = None
    #         self.stdout.write(u'\t\t{0:s}'.format(title))
    #         category, created = PuputCategory.objects.update_or_create(name=title, defaults={
    #             'slug': slug, 'parent': categories.get(parent)
    #         })
    #         categories[title] = category
    #     return categories

    # def import_entry_tags(self, tags, page):
    #     self.stdout.write("\tImporting tags...")
    #     for tag in tags:
    #         domain = tag.attrib.get('domain', 'category')
    #         if 'tag' in domain and tag.attrib.get('nicename'):
    #             self.stdout.write(u'\t\t{}'.format(tag.text))
    #             puput_tag, created = PuputTag.objects.update_or_create(name=tag.text)
    #             page.entry_tags.add(PuputTagEntryPage(tag=puput_tag))

    # def import_entry_categories(self, category_nodes, page):
    #     for category_node in category_nodes:
    #         domain = category_node.attrib.get('domain')
    #         if domain == 'category':
    #             puput_category = PuputCategory.objects.get(name=category_node.text)
    #             PuputCategoryEntryPage.objects.get_or_create(category=puput_category, page=page)

    def import_entry(self, title, content, items, item_node):
        creation_date = datetime.strptime(item_node.find(u'{{{0:s}}}post_date'.format(WP_NS)).text, '%Y-%m-%d %H:%M:%S')
        if settings.USE_TZ:
            creation_date = timezone.make_aware(creation_date, pytz.timezone('GMT'))

        excerpt = strip_tags(item_node.find(u'{{{0:s}excerpt/}}encoded'.format(WP_NS)).text or '')
        if not excerpt and content:
            excerpt = Truncator(strip_tags(content)).words(50)
        slug = slugify(title)[:255] or u'post-{0:s}'.format(item_node.find(u'{{{0:s}}}post_id'.format(WP_NS)).text)
        creator = item_node.find('{http://purl.org/dc/elements/1.1/}creator').text

        # Create page
        try:
            page = StandardPage.objects.get(slug=slug)
        except StandardPage.DoesNotExist:
            page = StandardPage(
                title=title,
                body=content,
                # excerpt=strip_tags(excerpt),
                slug=slug,
                go_live_at=datetime.strptime(item_node.find(u'{{{0:s}}}post_date_gmt'.format(WP_NS)).text,
                                             '%Y-%m-%d %H:%M:%S'),
                first_published_at=creation_date,
                # date=creation_date,
                owner=self.authors.get(creator),
                seo_title=title,
                search_description=excerpt,
                live=item_node.find(u'{{{0:s}}}status'.format(WP_NS)).text == 'publish')
            self.blogpage.add_child(instance=page)
            revision = self.blogpage.save_revision()
            revision.publish()
        # self.import_entry_tags(item_node.findall('category'), page)
        # self.import_entry_categories(item_node.findall('category'), page)
        # Import header image
        # image_id = self.find_image_id(item_node.findall(u'{{{0:s}}}postmeta'.format(WP_NS)))
        # if image_id:
            # self.import_header_image(page, items, image_id)
        page.save()
        page.save_revision(changed=False)

    # def find_image_id(self, metadatas):
        # for meta in metadatas:
        #     if meta.find(u'{{{0:s}}}meta_key'.format(WP_NS)).text == '_thumbnail_id':
        #         return meta.find(u'{{{0:s}}}meta_value'.format(WP_NS)).text

    def import_entries(self, items):
        self.stdout.write("Importing entries...")

        for item_node in items:
            title = (item_node.find('title').text or '')[:255]
            post_type = item_node.find(u'{{{0:s}}}post_type'.format(WP_NS)).text
            print (post_type)
            content = item_node.find('{http://purl.org/rss/1.0/modules/content/}encoded').text
            print (content)

            if post_type == 'post' and content and title:
                self.stdout.write(u'\t{0:s}'.format(title))
                # content = self.process_content_image(content)
                self.import_entry(title, content, items, item_node)

    # def _import_image(self, image_url):
        # img = NamedTemporaryFile(delete=True)
        # img.write(requests.get(image_url).content)
        # img.flush()
        # return img

    # def import_header_image(self, entry, items, image_id):
        # self.stdout.write('\tImport header images....')
        # for item in items:
        #     post_type = item.find(u'{{{0:s}}}post_type'.format(WP_NS)).text
        #     if post_type == 'attachment' and item.find(u'{{{0:s}}}post_id'.format(WP_NS)).text == image_id:
        #         title = item.find('title').text
        #         image_url = item.find(u'{{{0:s}}}attachment_url'.format(WP_NS)).text
        #         img = self._import_image(image_url)
        #         new_image = WagtailImage(file=File(file=img, name=title), title=title)
        #         new_image.save()
        #         entry.header_image = new_image
        #         entry.save()

    # def process_content_image(self, content):
        # self.stdout.write('\tGenerate and replace entry content images....')
        # if content:
        #     print (content)
        #     root = ET.fromstring(content)
        #     print (root)
        #     for el in root.iter('img'):
        #         parent_node = next(el.iterancestors())
        #         if 'wp-content' in el.attrib['src'] or 'files' in el.attrib['src']:
        #             img = self._import_image(el.attrib['src'])
        #             title = el.attrib.get('title') or el.attrib.get('alt')
        #             new_image = WagtailImage(file=File(file=img, name=title), title=title)
        #             new_image.save()
        #             el.attrib['src'] = new_image.get_rendition('original').file.url
        #             parent_node.attrib['href'] = new_image.get_rendition('original').file.url
        #             self.stdout.write(u'\t\t{}'.format(el.attrib['src']))
        #     # New content with images replaced
        #     content = ET.tostring(root, pretty_print=True).decode('utf-8')
        # # return content
