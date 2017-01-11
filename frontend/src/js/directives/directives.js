// define directives here

(function() {

    'use strict'

    // dynamic header directive
    angular
        .module('evalai')
        .directive('dynHeader', dynHeader);

    function dynHeader() {
        var directive = {
            link: link,
            templateUrl: 'dist/views/web/partials/dyn-header.html',
            transclude: true,
            restrict: 'EA'
        };
        return directive;

        function link(scope, element, attrs) {

            function headerComp() {
                var self = this;
                this.init();
            };

            headerComp.prototype = {
                init: function() {
                    var self = this;

                    // initialized mobile sidebar
                    angular.element(".button-collapse").sideNav({
                        menuWidth: 200,
                        closeOnClick: true,
                        draggable: true
                    });

                }
            };

            var headerObj = new headerComp();
        }
    }

})();

// loader directive

(function() {

    'use strict'
    angular
        .module('evalai')
        .directive('evalLoader', evalLoader);

    function evalLoader() {

        var directive = {
            link: link,
            templateUrl: 'dist/views/web/partials/loader.html',
            transclude: true,
            restrict: 'EA'
        };
        return directive;

        function link(scope, element, attrs) {

            function evalLoader() {
                var self = this;
                this.init();
            };

            evalLoader.prototype = {
                init: function() {


                }
            };

            var evalLoaderObj = new evalLoader();
        }
    }

})();

// simple loader directive

(function() {

    'use strict'
    angular
        .module('evalai')
        .directive('simLoader', simLoader);

    function simLoader() {

        var directive = {
            link: link,
            templateUrl: 'dist/views/web/partials/sim-loader.html',
            transclude: true,
            restrict: 'EA'
        };
        return directive;

        function link(scope, element, attrs) {

            function loaderComp() {
                var self = this;
                this.init();
            };

            loaderComp.prototype = {
                init: function() {
                    angular.element("#sim-loader").hide();

                }
            };

            var loaderCompObj = new loaderComp();
        }
    }

})();

//Sidebar in Dashboard      

(function() {

    'use strict'

    // dynamic header directive       
    angular
        .module('evalai')
        .directive('sideBar', sideBar);

    function sideBar() {
        var directive = {
            link: function() {
                //do nothing      
            },
            templateUrl: 'dist/views/web/partials/sidebar.html',
            transclude: true,
            restrict: 'EA'
        };
        return directive;
    }

})();


//Dashboard header
(function() {

    'use strict'

    // dynamic header directive
    angular
        .module('evalai')
        .directive('simHeader', simHeader);

    function simHeader() {
        var directive = {
            link: link,
            templateUrl: 'dist/views/web/partials/sim-header.html',
            transclude: true,
            restrict: 'EA'
        };
        return directive;

        function link(scope, element, attrs) {

            function headerComp() {
                var self = this;
                this.init();
            };

            headerComp.prototype = {
                init: function() {
                    var self = this;

                    // initialized mobile sidebar
                    angular.element(".button-collapse").sideNav({
                        menuWidth: 200,
                        closeOnClick: true,
                        draggable: true
                    });

                }
            };

            var headerObj = new headerComp();
        }
    }

})();

// scroll directive

(function() {

    'use strict'

    // dynamic header directive
    angular
        .module('evalai')
        .directive('scrollShadow', scrollShadow);

    function scrollShadow() {

        var directive = {
            link: link,
            // template : ' <div class="w-400 side-logo">EvalAI</div><div class="w-300 text-light-gray">{{web.name}} <i class="fa fa-caret-down"></i></div>',
            transclude: true,
            restrict: 'EA'
        };
        return directive;

        function link(scope, element, attrs) {

            function shadowComp() {
                var self = this;
                this.init();
            };

            shadowComp.prototype = {
                init: function() {
                    var self = this;

                    // initialized mobile sidebar
                    angular.element(".links-section-outer").bind('scroll', function() {
                        // alert("")
                        if (this.scrollTop >= 5) {
                            angular.element(".side-intro").addClass('z-depth-3');
                        } else {
                            angular.element(".side-intro").removeClass('z-depth-3')
                        }
                        scope.$apply();
                    });

                }
            };

            var shadowCompObj = new shadowComp();
        }
    }

})();

// profile directive slider component

(function() {

    'use strict'

    // dynamic header directive
    angular
        .module('evalai')
        .directive('slideProfile', slideProfile);

    function slideProfile() {

        var directive = {
            link: link,
            transclude: true,
            restrict: 'EA'
        };
        return directive;

        function link(scope, element, attrs) {

            function slideComp() {
                var self = this;
                this.init();
            };

            slideComp.prototype = {
                init: function() {
                    var self = this;
                    // initialized mobile sidebar
                    angular.element(".profile-sidebar").animate({
                        'left': '219px'
                    }, 200)

                }
            };

            var slideCompObj = new slideComp();
        }
    }
    
})();