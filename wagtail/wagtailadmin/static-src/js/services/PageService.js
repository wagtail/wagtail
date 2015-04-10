// A stub service for getting the nav structure
const PageService = function() {

}

PageService.prototype = {
    getPageTypes(callback) {
        callback({
            data: [
                {
                    type:           "site.HomePage",
                    verbose_name:   "Home Page",
                    subpage_types:  [
                        'site.StandardPage',
                        'site.ContactPage',
                        'site.IndexPage',
                        'site.FormPage',
                        'site.BlogPostPage',
                        'site.BlogPostIndexPage',
                        'site.PersonPage',
                        'site.PersonIndexPage'
                    ]
                },
                {
                    type:           "site.StandardPage",
                    verbose_name:   "Standard Page",
                    subpage_types:  [
                        'site.StandardPage',
                        'site.IndexPage',
                        'site.PersonPage',
                        "site.PersonIndexPage"
                    ],
                },
                {
                    type:           'site.ContactPage',
                    verbose_name:   "Contact Page",
                    subpage_types:  [
                        'site.PersonPage',
                        "site.AddressPage",
                        "site.MapPage"
                    ],
                },
                {
                    type:           'site.IndexPage',
                    verbose_name:   "Index Page",
                    subpage_types:  [
                        'site.StandardPage'
                    ]
                },
                {
                    type:           'site.FormPage',
                    verbose_name:   "Form Page",
                    subpage_types:  [
                        'site.StandardPage'
                    ]
                },
                {
                    type:           'site.BlogPostPage',
                    verbose_name:   "Blog Post"
                },
                {
                    type:           'site.BlogPostIndexPage',
                    verbose_name:   "Blog Landing Page",
                    subpage_types:  [
                        'site.BlogPostPage'
                    ]
                },
                {
                    type:           'site.PersonPage',
                    verbose_name:   "Person Page",
                    subpage_types:  []
                },
                {
                    type:           'site.PersonIndexPage',
                    verbose_name:   "Person Index Page",
                    subpage_types:  [
                        'site.PersonPage'
                    ]
                },
                {
                    type:           'site.AddressPage',
                    verbose_name:   "Address Page",
                    subpage_types:  [
                        'site.MapPage'
                    ]
                },
                {
                    type:           'site.RootPage',
                    verbose_name:   'Site Root',
                    subpage_types:  [
                        "site.HomePage"
                    ]
                },
                {
                    type:           'site.ProductIndexPage',
                    verbose_name:   'Product Index Page',
                    subpage_types:  [
                        "site.ProductPage"
                    ]
                },
                {
                    type:           'site.ProductPage',
                    verbose_name:   'Product Page',
                    subpage_types:  [
                        "site.StandardPage"
                    ]
                },
                {
                    type:           'site.MediaReleaseIndexPage',
                    verbose_name:   'Media Release Index Page',
                    subpage_types:  [
                        "site.MediaReleasePage",
                        "site.StandardPage"
                    ]
                },
                {
                    type:           'site.MediaReleasePage',
                    verbose_name:   'Media Release Page',
                    subpage_types:  []
                }
            ]
        });
    },
    fetch(callback) {
        var data = {
            name: "root",
            type:           'site.RootPage',
            children: [
            {
                name: "Welcome to your wagtail site",
                type: "site.HomePage",
                "slug": "home",
                path: ",",
                status: "live",
                children: [
                    {
                        name: "About us",
                        status: "live",
                        path: ",about-us",
                        type: "site.StandardPage",
                        children: [
                            {
                                name: "test page",
                                type: "site.StandardPage",
                            },
                            {
                                name: "other test page",
                                type: "site.StandardPage",
                                url: "/pages/about-us/other-test-page"
                            },
                            {
                                name: "our staff",
                                type: "site.PersonIndexPage",
                                children: [
                                    {
                                        name: "bob"
                                    },
                                    {
                                        name: "frank"
                                    }
                                ]
                            },
                            {
                                name: "some test data",
                                type: "site.StandardPage",
                                subpage_types: []
                            },
                            {
                                name: "some more test data",
                                type: "site.StandardPage",
                                subpage_types: []
                            },
                            {
                                name: "some test data",
                                type: "site.StandardPage",
                                subpage_types: []
                            },
                            {
                                name: "some more test data",
                                type: "site.StandardPage",
                                subpage_types: []
                            },
                            {
                                name: "some test data",
                                type: "site.StandardPage",
                                subpage_types: []
                            },
                            {
                                name: "some more test data",
                                type: "site.StandardPage",
                                subpage_types: []
                            },
                            {
                                name: "some test data",
                                type: "site.StandardPage",
                                subpage_types: []
                            },
                            {
                                name: "some more test data",
                                type: "site.StandardPage",
                                subpage_types: []
                            }
                        ]
                    },
                    {
                        name: "Products",
                        status: "draft",
                        type: "site.ProductIndexPage",
                        path: ",new-product-page"
                    },
                    {
                        name: "Terms and Conditions Page",
                        status: "draft",
                        path: ",ts-and-cs",
                        type: "site.StandardPage",
                        subpage_types: [
                            'site.StandardPage',
                        ],
                    },
                    {
                        name: "Media releases",
                        type: "site.MediaReleaseIndexPage",
                        status: "pending",
                        path: ",media-release"
                    }
                ]
            },{
                name: "Blog",
                type: "site.BlogPostIndexPage",
                subpage_types: [
                    'site.StandardPage',
                    'site.ContactPage',
                    'site.BlogPostPage',
                    'site.BlogPostIndexPage',
                    'site.PersonPage'
                ]
            }
            ]
        };
        var delay = this.getRandomTransportTime();

        setTimeout(() => {
            console.log("Waiting", delay + "ms", "to send some data");
            callback(data);
        }, delay);
    },
    getRandomTransportTime() {
        return Math.ceil(Math.random() * 900);
    },
    fetchChild(url, node, callback) {
        setTimeout(() => {
            callback({
                data: [
                    {
                        name: "test page", url: "/some-url/", children: [],
                        type: "site.StandardPage"
                    },
                    {
                        name: "other-test-page",
                        type: "site.StandardPage"
                    },
                    {
                        name: "other-other-test-page",
                        type: "site.StandardPage"
                    }
                ],
                url: url,
                node: node
            });
        }, this.getRandomTransportTime() * 4);
    }
}

export default PageService;

