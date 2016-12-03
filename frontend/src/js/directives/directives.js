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
