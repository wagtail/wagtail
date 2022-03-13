# Edit Page tabs

A common feature of the _Edit_ pages for all page types is the three tabs at the top of the screen. The first, _Content_, is where you build the content of the page itself.

## The Promote tab

The Promote tab is where you can configure a page's metadata, to help search engines find and index it. Below is a description of all the default fields under this tab.

**For Search Engines**

-   **Slug:** The section of the URL that appears after your website's domain e.g. `http://domain.com/blog/[my-slug]/`. This is automatically generated from the main page title, which is set in the Content tab. Slugs should be entirely lowercase, with words separated by hyphens (-). It is recommended that you don't change a page's slug once a page is published.
-   **Title tag:** This is the bold headline that often shows up search engine results. This is one of the most significant elements of how search engines rank the page. The keywords used here should align with the keywords you wish to be found for. If you don't think this field is working, ask your developers to check they have configured the site to output the appropriate tags on the frontend.
-   **Meta description:** This is the descriptive text displayed underneath a headline in search engine results. It is designed to explain what this page is about. It has no impact on how search engines rank your content, but it can impact on the likelihood that a user will click your result. Ideally 140 to 155 characters in length. If you don't think this field is working, ask your developers to check they have configured the site to output the appropriate tags on the frontend.

**For Site Menus**

-   **Show in menus:** Ticking this box will ensure that the page is included in automatically generated menus on your site. Note: A page will only display in menus if all of its parent pages also have _Show in menus_ ticked.

![](../../_static/images/screen26.5_promote_tab.png)

```{note}
You may see more fields than this in your promote tab. These are just the default fields, but you are free to add other fields to this section as necessary.
```

## The Settings Tab

The _Settings_ tab has three fields by default.

-   **Go Live date/time:** Sets the date and time at which the changes should go live when published. See [](scheduled_publishing) for more details.
-   **Expiry date/time:** Sets the date and time at which this page should be unpublished.
-   **Privacy:** Sets restrictions for who can view the page on the frontend. Also applies to all child pages.
