
angular
    .module('evalai')
    .service('stringToTemplate', stringToTemplate);

function stringToTemplate() {

    this.convert = function (endpoint, params) {

        var key = Object.keys(params)[0];
        var value = params[key];
        this.convertString = function(literal, params) {
            return new Function(params, "return `"+literal+"`;");
        };

        let template = this.convertString(endpoint, key);

        let url  = template(value);
        return url;
    };

    return this;
}

