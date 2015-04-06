// A stub service for getting the nav structure
var PageService = function() {

}

PageService.prototype = {
    fetch: function(url) {

        if (url) {
            return [
                {
                    "name": "some test data"
                },
                {
                    "name": "some more test data"
                }
            ];
        }


        var data = {
            "name": "root",
            "children": [
            {
                "name": "Welcome to your wagtail site",
                "slug": "home",
                "path": ",",
                "status": "live",
                "children": [
                    {
                        "name": "About us",
                        "status": "live",
                        "path": ",about-us",
                        "children": [
                            {
                                "name": "test page"
                            },
                            {
                                "name": "other test page",
                                "url": "/pages/about-us/other-test-page"
                            },
                            {
                                "name": "our staff",
                                "children": [
                                    {
                                        "name": "bob"
                                    },
                                    {
                                        "name": "frank"
                                    }
                                ]
                            },
                            {
                                "name": "some test data"
                            },
                            {
                                "name": "some more test data"
                            },
                            {
                                "name": "some test data"
                            },
                            {
                                "name": "some more test data"
                            },
                            {
                                "name": "some test data"
                            },
                            {
                                "name": "some more test data"
                            },
                            {
                                "name": "some test data"
                            },
                            {
                                "name": "some more test data"
                            }
                        ]
                    },
                    {
                        "name": "New product page",
                        "status": "draft",
                        "path": ",new-product-page"
                    },
                    {
                        "name": "Media release",
                        "status": "pending",
                        "path": ",media-release"
                    }
                ]
            },{
                "name": "Some other top level page"
            }
            ]
        };

        return data;
        // var delay = Math.ceil(Math.random() * 300);
        // var delay = 0;
        // setTimeout(function() {
        //     console.log(delay);
        //     callback(data);
        // }, delay);
    }
}


module.exports = PageService;

