from django.db import migrations


def create_homepage(apps, schema_editor):
    # Get models
    ContentType = apps.get_model("contenttypes.ContentType")
    Page = apps.get_model("wagtailcore.Page")
    Site = apps.get_model("wagtailcore.Site")
    HomePage = apps.get_model("home.HomePage")

    # Delete the default homepage (of type Page) as created by wagtailcore.0002_initial_data,
    # if it exists
    page_content_type = ContentType.objects.get(
        model="page", app_label="wagtailcore"
    )
    Page.objects.filter(
        content_type=page_content_type, slug="home", depth=2
    ).delete()

    # Create content type for homepage model
    homepage_content_type, __ = ContentType.objects.get_or_create(
        model="homepage", app_label="home"
    )

    # Create a new homepage
    homepage = HomePage.objects.create(
        title="Home",
        draft_title="Home",
        slug="home",
        content_type=homepage_content_type,
        path="00010001",
        depth=2,
        numchild=0,
        url_path="/home/",
        body="""
        <header class="header">
            <div class="logo">
                <a href="https://wagtail.org/">
                    <svg class="figure-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 342.5 126.2">
                        <title>"Visit the Wagtail website"</title>
                        <path fill="#FFF"
                            d="M84 1.9v5.7s-10.2-3.8-16.8 3.1c-4.8 5-5.2 10.6-3 18.1 21.6 0 25 12.1 25 12.1L87 27l6.8-8.3c0-9.8-8.1-16.3-9.8-16.8z" />
                        <circle cx="85.9" cy="15.9" r="2.6" />
                        <path
                            d="M89.2 40.9s-3.3-16.6-24.9-12.1c-2.2-7.5-1.8-13 3-18.1C73.8 3.8 84 7.6 84 7.6V1.9C80.4.3 77 0 73.2 0 59.3 0 51.6 10.4 48.3 17.4L9.2 89.3l11-2.1-20.2 39 14.1-2.5L24.9 93c30.6 0 69.8-11 64.3-52.1z" />
                        <path d="M102.4 27l-8.6-8.3L87 27z" />
                        <path fill="#FFF"
                            d="M30 84.1s1-.2 2.8-.6c1.8-.4 4.3-1 7.3-1.8 1.5-.4 3.1-.9 4.8-1.5 1.7-.6 3.5-1.2 5.2-2 1.8-.7 3.6-1.6 5.4-2.6 1.8-1 3.5-2.1 5.1-3.4.4-.3.8-.6 1.2-1l1.2-1c.7-.7 1.5-1.4 2.2-2.2.7-.7 1.3-1.5 1.9-2.3l.9-1.2.4-.6.4-.6c.2-.4.5-.8.7-1.2.2-.4.4-.8.7-1.2l.3-.6.3-.6c.2-.4.4-.8.5-1.2l.9-2.4c.2-.8.5-1.6.7-2.3.2-.7.3-1.5.5-2.1.1-.7.2-1.3.3-2 .1-.6.2-1.2.2-1.7.1-.5.1-1 .2-1.5.1-1.8.1-2.8.1-2.8l1.6.1s-.1 1.1-.2 2.9c-.1.5-.1 1-.2 1.5-.1.6-.1 1.2-.3 1.8-.1.6-.3 1.3-.4 2-.2.7-.4 1.4-.6 2.2-.2.8-.5 1.5-.8 2.4-.3.8-.6 1.6-1 2.5l-.6 1.2-.3.6-.3.6c-.2.4-.5.8-.7 1.3-.3.4-.5.8-.8 1.2-.1.2-.3.4-.4.6l-.4.6-.9 1.2c-.7.8-1.3 1.6-2.1 2.3-.7.8-1.5 1.4-2.3 2.2l-1.2 1c-.4.3-.8.6-1.3.9-1.7 1.2-3.5 2.3-5.3 3.3-1.8.9-3.7 1.8-5.5 2.5-1.8.7-3.6 1.3-5.3 1.8-1.7.5-3.3 1-4.9 1.3-3 .7-5.6 1.3-7.4 1.6-1.6.6-2.6.8-2.6.8z" />
                        <g fill="#231F20">
                            <path
                                d="M127 83.9h-8.8l-12.6-36.4h7.9l9 27.5 9-27.5h7.9l9 27.5 9-27.5h7.9L153 83.9h-8.8L135.6 59 127 83.9zM200.1 83.9h-7V79c-3 3.6-7 5.4-12.1 5.4-3.8 0-6.9-1.1-9.4-3.2s-3.7-5-3.7-8.6c0-3.6 1.3-6.3 4-8 2.6-1.8 6.2-2.7 10.7-2.7h9.9v-1.4c0-4.8-2.7-7.3-8.1-7.3-3.4 0-6.9 1.2-10.5 3.7l-3.4-4.8c4.4-3.5 9.4-5.3 15.1-5.3 4.3 0 7.8 1.1 10.5 3.2 2.7 2.2 4.1 5.6 4.1 10.2v23.7zm-7.7-13.6v-3.1h-8.6c-5.5 0-8.3 1.7-8.3 5.2 0 1.8.7 3.1 2.1 4.1 1.4.9 3.3 1.4 5.7 1.4 2.4 0 4.6-.7 6.4-2.1 1.8-1.3 2.7-3.1 2.7-5.5zM241.7 47.5v31.7c0 6.4-1.7 11.3-5.2 14.5-3.5 3.2-8 4.8-13.4 4.8-5.5 0-10.4-1.7-14.8-5.1l3.6-5.8c3.6 2.7 7.1 4 10.8 4 3.6 0 6.5-.9 8.6-2.8 2.1-1.9 3.2-4.9 3.2-9v-4.7c-1.1 2.1-2.8 3.9-4.9 5.1-2.1 1.3-4.5 1.9-7.1 1.9-4.8 0-8.8-1.7-11.9-5.1-3.1-3.4-4.7-7.6-4.7-12.6s1.6-9.2 4.7-12.6c3.1-3.4 7.1-5.1 11.9-5.1 4.8 0 8.7 2 11.7 6v-5.4h7.5zm-28.4 16.8c0 3 .9 5.6 2.8 7.7 1.8 2.2 4.3 3.2 7.5 3.2 3.1 0 5.7-1 7.6-3.1 1.9-2.1 2.9-4.7 2.9-7.8 0-3.1-1-5.8-2.9-7.9-2-2.2-4.5-3.2-7.6-3.2-3.1 0-5.6 1.1-7.4 3.4-2 2.1-2.9 4.7-2.9 7.7zM260.9 53.6v18.5c0 1.7.5 3.1 1.4 4.1.9 1 2.2 1.5 3.8 1.5 1.6 0 3.2-.8 4.7-2.4l3.1 5.4c-2.7 2.4-5.7 3.6-8.9 3.6-3.3 0-6-1.1-8.3-3.4-2.3-2.3-3.5-5.3-3.5-9.1V53.6h-4.6v-6.2h4.6V36.1h7.7v11.4h9.6v6.2h-9.6zM309.5 83.9h-7V79c-3 3.6-7 5.4-12.1 5.4-3.8 0-6.9-1.1-9.4-3.2s-3.7-5-3.7-8.6c0-3.6 1.3-6.3 4-8 2.6-1.8 6.2-2.7 10.7-2.7h9.9v-1.4c0-4.8-2.7-7.3-8.1-7.3-3.4 0-6.9 1.2-10.5 3.7l-3.4-4.8c4.4-3.5 9.4-5.3 15.1-5.3 4.3 0 7.8 1.1 10.5 3.2 2.7 2.2 4.1 5.6 4.1 10.2v23.7zm-7.7-13.6v-3.1h-8.6c-5.5 0-8.3 1.7-8.3 5.2 0 1.8.7 3.1 2.1 4.1 1.4.9 3.3 1.4 5.7 1.4 2.4 0 4.6-.7 6.4-2.1 1.8-1.3 2.7-3.1 2.7-5.5zM319.3 40.2c-1-1-1.4-2.1-1.4-3.4 0-1.3.5-2.5 1.4-3.4 1-1 2.1-1.4 3.4-1.4 1.3 0 2.5.5 3.4 1.4 1 1 1.4 2.1 1.4 3.4 0 1.3-.5 2.5-1.4 3.4s-2.1 1.4-3.4 1.4c-1.3.1-2.4-.4-3.4-1.4zm7.2 43.7h-7.7V47.5h7.7v36.4zM342.5 83.9h-7.7V33.1h7.7v50.8z" />
                        </g>
                    </svg>
                </a>
            </div>
            <div class="header-link">
                This works for all cases but prerelease versions:
                <a href="https://docs.wagtail.org/en/stable/releases/">
                    "View the release notes"
                </a>
            </div>
        </header>
        <main class="main">
            <div class="figure">
                <svg class="figure-space" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" aria-hidden="true">
                    <path class="egg" fill="currentColor"
                        d="M150 250c-42.741 0-75-32.693-75-90s42.913-110 75-110c32.088 0 75 52.693 75 110s-32.258 90-75 90z" />
                    <ellipse fill="#ddd" cx="150" cy="270" rx="40" ry="7" />
                </svg>
            </div>
            <div class="main-text"
                style="max-width: 800px; margin: 0 auto; text-align: left; background: #fff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); color: #333; line-height: 1.8;">
                <h1
                    style="color: #2F3941; text-align: center; border-bottom: 2px solid #EEE; padding-bottom: 20px; margin-bottom: 30px;">
                    "Your Wagtail Journey Starts Here!"</h1>

                <p style="font-size: 1.1rem;">"Welcome! You're looking at the default Wagtail welcome screen. This page
                    is beautiful, but it's temporary. Wagtail is a CMS designed to let you build whatever you want. Here is a
                    definitive guide to taking control of your new site, step by step."</p>

                <div style="background: #eaf1f1; border-left: 4px solid #167e7c; padding: 15px 20px; margin: 25px 0;">
                    <p style="margin: 0;"><strong>"Did you know?"</strong> "Wagtail separates your content
                        structure (using Python) from how it looks (using HTML). This makes your website incredibly fast and
                        flexible."</p>
                </div>

                <h2 style="color: #167e7c; margin-top: 40px; font-size: 1.5rem;">"Step 1: Understand Your Homepage"
                </h2>
                <p>"Right now, your site doesn't have an active Homepage. However, Wagtail has already created the
                    files you need to build one:"</p>
                <ul style="list-style-type: disc; margin-left: 20px; margin-bottom: 25px;">
                    <li><strong>"The Logic"</strong>: <code>home/models.py</code></li>
                    <li><strong>"The Visuals"</strong>: <code>home/templates/home/home_page.html</code></li>
                </ul>

                <h2 style="color: #167e7c; margin-top: 40px; font-size: 1.5rem;">"Step 2: Add Content Fields to Your
                    Model"</h2>
                <p>"By default, a Wagtail" <code>Page</code> "only has a Title. To add things like a rich
                    text editor (for blogs, images, and videos), you edit your Python models. Open"
                    <code>home/models.py</code> "and add:"
                </p>

                <pre
                    style="background: #2b303b; color: #c0c5ce; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 0.9rem; line-height: 1.5;"><code>from wagtail.models import Page
        from wagtail.fields import RichTextField
        from wagtail.admin.panels import FieldPanel

        class HomePage(Page):
            # This creates a database column for your content!
            body = RichTextField(blank=True)

            # This tells the Wagtail Admin to show an editor for 'body'
            content_panels = Page.content_panels + [
                FieldPanel('body')
            ]</code></pre>

                <h2 style="color: #167e7c; margin-top: 40px; font-size: 1.5rem;">"Step 3: Tell the Database About Your
                    Changes"</h2>
                <p>"Every time you edit something in" <code>models.py</code>, "you must tell the database
                    to create columns for your new fields. Stop your server and run these commands in your terminal:"</p>
                <pre
                    style="background: #2b303b; color: #c0c5ce; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 0.9rem; line-height: 1.5;"><code>python manage.py makemigrations
        python manage.py migrate</code></pre>

                <h2 style="color: #167e7c; margin-top: 40px; font-size: 1.5rem;">"Step 4: Create a Superuser & Use the
                    Admin"</h2>
                <p>"To actually write your content and upload photos, you need an account. Run:"</p>
                <pre
                    style="background: #2b303b; color: #c0c5ce; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 0.9rem; line-height: 1.5;"><code>python manage.py createsuperuser</code></pre>
                <p>"Then click the "<strong>Admin Interface</strong>" link below. Log in, go to "
                    <strong>Pages > Root</strong>", click 'Add child page', select 'Home Page', write your text, and
                    hit Publish! Don't forget to go to "<strong>Settings > Sites</strong>" to map 'localhost' to
                    your new Home Page."
                </p>

                <h2 style="color: #167e7c; margin-top: 40px; font-size: 1.5rem;">"Step 5: Display It On The Web"
                </h2>
                <p>"Now that your content is saved, you need to show it! Open"
                    <code>home/templates/home/home_page.html</code>. "Delete the line that includes this welcome
                    screen, load the Wagtail tags, and drop in your body field:"
                </p>
                <pre
                    style="background: #2b303b; color: #c0c5ce; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 0.9rem; line-height: 1.5;"><code>&#123;% extends "base.html" %&#125;
        &#123;% load wagtailcore_tags %&#125;

        &#123;% block content %&#125;
            &lt;h1&gt;&#123;&#123; page.title &#125;&#125;&lt;/h1&gt;
            &lt;div class="content"&gt;
                &#123;&#123; page.body|richtext &#125;&#125;
            &lt;/div&gt;
        &#123;% endblock content %&#125;</code></pre>

                <p style="text-align: center; margin-top: 50px; font-size: 1.2rem; font-weight: bold;">"Happy
                    configuring! Your journey into powerful, elegant content management has just begun."</p>
            </div>
        </main>
        <footer class="footer" role="contentinfo">
            <a class="option option-one" href="https://docs.wagtail.org/">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">
                    <path
                        d="M9 21c0 .5.4 1 1 1h4c.6 0 1-.5 1-1v-1H9v1zm3-19C8.1 2 5 5.1 5 9c0 2.4 1.2 4.5 3 5.7V17c0 .5.4 1 1 1h6c.6 0 1-.5 1-1v-2.3c1.8-1.3 3-3.4 3-5.7 0-3.9-3.1-7-7-7zm2.9 11.1l-.9.6V16h-4v-2.3l-.9-.6C7.8 12.2 7 10.6 7 9c0-2.8 2.2-5 5-5s5 2.2 5 5c0 1.6-.8 3.2-2.1 4.1z" />
                </svg>
                <div>
                    <h2>"Wagtail Documentation"</h2>
                    <p>"Topics, references, & how-tos"</p>
                </div>
            </a>
            <a class="option option-two" href="https://docs.wagtail.org/en/stable/getting_started/tutorial.html">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M0 0h24v24H0V0z" fill="none" />
                    <path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z" />
                </svg>
                <div>
                    <h2>"Tutorial"</h2>
                    <p>"Build your first Wagtail site"</p>
                </div>
            </a>
            <a class="option option-three" href="/admin/">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M0 0h24v24H0z" fill="none" />
                    <path
                        d="M16.5 13c-1.2 0-3.07.34-4.5 1-1.43-.67-3.3-1-4.5-1C5.33 13 1 14.08 1 16.25V19h22v-2.75c0-2.17-4.33-3.25-6.5-3.25zm-4 4.5h-10v-1.25c0-.54 2.56-1.75 5-1.75s5 1.21 5 1.75v1.25zm9 0H14v-1.25c0-.46-.2-.86-.52-1.22.88-.3 1.96-.53 3.02-.53 2.44 0 5 1.21 5 1.75v1.25zM7.5 12c1.93 0 3.5-1.57 3.5-3.5S9.43 5 7.5 5 4 6.57 4 8.5 5.57 12 7.5 12zm0-5.5c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2zm9 5.5c1.93 0 3.5-1.57 3.5-3.5S18.43 5 16.5 5 13 6.57 13 8.5s1.57 3.5 3.5 3.5zm0-5.5c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2z" />
                </svg>
                <div>
                    <h2>"Admin Interface "</h2>
                    <p>"Create your superuser first!"</p>
                </div>
            </a>
        </footer>"""
    )

    # Create a site with the new homepage set as the root
    Site.objects.create(hostname="localhost", root_page=homepage, is_default_site=True)


def remove_homepage(apps, schema_editor):
    # Get models
    ContentType = apps.get_model("contenttypes.ContentType")
    HomePage = apps.get_model("home.HomePage")

    # Delete the default homepage
    # Page and Site objects CASCADE
    HomePage.objects.filter(slug="home", depth=2).delete()

    # Delete content type for homepage model
    ContentType.objects.filter(model="homepage", app_label="home").delete()


class Migration(migrations.Migration):

    run_before = [
        ("wagtailcore", "0053_locale_model"),
    ]

    dependencies = [
        ("home", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_homepage, remove_homepage),
    ]
