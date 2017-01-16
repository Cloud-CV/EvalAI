(function() {

    'use strict';

    angular
        .module('evalai')
        .service('validationSvc', validationSvc);


    function validationSvc() {
        // factory for password check
        this.password_check = function(password1, password2) {
            var password1_len = password1.length;
            var password2_len = password2.length;
            var context = {};

            if (password1_len >= 8 && password2_len >= 8) {
                if (password1 === password2) {
                    context.confirmMsg = "Passwords Match !";
                    context.status = true;
                    return context;
                } else {
                    context.confirmMsg = "Passwords do not Match !";
                    context.status = false;
                    return context;
                }
            } else {
                context.confirmMsg = "Password is less than 8 characters !";
                context.status = false;
                return context;
            }
        };
    }

})();
