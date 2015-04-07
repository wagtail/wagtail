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
                                "url": "/pages/about-us/other-test-page",
                                "children": []
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
                                "name": "some test data",
                                "children": []
                            },
                            {
                                "name": "some more test data",
                                "children": []
                            },
                            {
                                "name": "some test data",
                                "children": []
                            },
                            {
                                "name": "some more test data",
                                "children": []
                            },
                            {
                                "name": "some test data",
                                "children": []
                            },
                            {
                                "name": "some more test data",
                                "children": []
                            },
                            {
                                "name": "some test data",
                                "children": []
                            },
                            {
                                "name": "some more test data",
                                "children": []
                            }
                        ]
                    },
                    {
                        "name": "New product page",
                        "status": "draft",
                        "path": ",new-product-page",
                        "children": []
                    },
                    {
                        "name": "Media release",
                        "status": "pending",
                        "path": ",media-release",
                        "children": []
                    }
                ]
            },{
                "name": "Some other top level page",
                "children": []
            }
            ]
        };


        // function decorate(item) {

        // }

        return data;
        // var delay = Math.ceil(Math.random() * 300);
        // var delay = 0;
        // setTimeout(function() {
        //     console.log(delay);
        //     callback(data);
        // }, delay);
    }
}


export default PageService;

// module.exports = pageeService;

