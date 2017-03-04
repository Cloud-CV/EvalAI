var compareTo = function() {
    return {
        require: "ngModel",
        scope: {
            otherModelValue: "=compareTo"
        },
        link: function(scope, element, attributes, ngModel) {

            ngModel.$validators.compareTo = function(modelValue) {
                return modelValue == scope.otherModelValue;
            };

            scope.$watch("otherModelValue", function() {
                ngModel.$validate();
            });
        }
    };
};
var match = function() {
    return {
        require: "ngModel",
        scope: {
            otherModelValue: "=match"
        },
        link: function(scope, element, attributes, ngModel) {

            ngModel.$validators.match = function(modelValue) {
                return modelValue != scope.otherModelValue;
            };

            scope.$watch("otherModelValue", function() {
                ngModel.$validate();
            });
        }
    };
};

angular
    .module('evalai')
    .directive("compareTo", compareTo)
    .directive("match", match);
