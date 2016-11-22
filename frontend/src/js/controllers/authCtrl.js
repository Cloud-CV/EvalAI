// Invoking IIFE for auth

(function(){

	'use strict';

	angular
	    .module('evalai')
	    .controller('AuthCtrl', AuthCtrl);

	AuthCtrl.$inject = ['utilities', '$state'];

    function AuthCtrl(utilities, $state){
    	var vm = this;
    	
    	vm.isRem = false;
    	// getUser for signup
    	vm.regUser={};
    	// useDetails for login
    	vm.getUser={};

    	// default parameters
    	vm.isLoader = false;
    	vm.isPassConf = true;
    	vm.wrnMsg = {};
    	vm.isValid = {};
    	vm.confirmMsg = '';
    	vm.loaderTitle = '';
    	vm.loginContainer = angular.element('.auth-container');

    	// show loader
    	vm.startLoader = function(msg){
    		vm.isLoader = true;
    		vm.loaderTitle = msg;
    		vm.loginContainer.addClass('low-screen');
    	}

    	// stop loader
    	vm.stopLoader = function(){
    		vm.isLoader = false;
    		vm.loaderTitle = '';
			vm.loginContainer.removeClass('low-screen');
    	}

    	// getting signup
    	vm.userSignUp = function(){
    		vm.isValid = {};
    		var msg = "Setting up your details!"
			vm.startLoader(msg);

			// call utility service
    		var parameters = {};
			parameters.url = 'auth/registration/';
			parameters.method = 'POST';
			parameters.data = {
				"username": vm.regUser.name,
	  		 	"password1": vm.regUser.password,
	  		 	"password2": vm.regUser.confirm,
	  		 	"email": vm.regUser.email
			}
			parameters.callback = {
				onSuccess: function(response, status){
					if(status == 201){
						vm.regUser= {};
						vm.wrnMsg = {};
    					vm.isValid = {};
						vm.confirmMsg=''
						vm.regMsg = "Registered successfully, Login to continue!";
						$state.go('auth.login');
						vm.stopLoader();
					}
					else{
						alert("Network Problem");
					}
				},
				onError : function(error, status){
					if(status == 400){
						vm.stopLoader();
						vm.isConfirm = false;
						vm.confirmMsg = "Please correct above marked fields!"
						angular.forEach(error, function(value, key){
							if(key=='email'){
								vm.isValid.email=true;
								vm.wrnMsg.email = value[0]
							}
							if(key=='password1'){
								vm.isValid.password=true;
								vm.wrnMsg.password = value[0];
							}
							if(key=='password2' || key=='non_field_errors'){
								vm.isValid.confirm=true;
								vm.wrnMsg.confirm = value[0];
							}
							if(key=='username'){
								vm.isValid.username=true;
								vm.wrnMsg.username = value[0];
							}
						})
					}
				}
			};

			utilities.sendRequest(parameters, "no-header");
    	}

    	// login user
    	vm.userLogin = function(){
    		vm.isValid = {};
    		var token = null;
    		console.log(vm.isRem);
    		var msg = "Taking you to EvalAI!"
			vm.startLoader(msg);

			// call utility service
    		var parameters = {};
			parameters.url = 'auth/login/';
			parameters.method = 'POST';
			parameters.data = {
				"username": vm.getUser.name,
	  		 	"password": vm.getUser.password,
			}
			parameters.callback = {
				onSuccess: function(response, status){
					if(status == 200){
						vm.getUser= {};
						vm.wrnMsg = {};
    					vm.isValid = {};
						vm.confirmMsg=''
						vm.regMsg = "";
						utilities.storeData('userKey', response.key);
						utilities.storeData('isRem', vm.isRem);
						token = response.key;
						utilities.isAuthenticated();
						$state.go('web.dashboard');

						vm.stopLoader();
					}
					else{
						alert("Something went wrong");
						vm.stopLoader();
					}
				},
				onError : function(error, status){
					if(status == 400){
						vm.stopLoader();
						vm.isConfirm = false;
						vm.wrnMsg.cred = "Please correct above marked fields!"
						angular.forEach(error, function(value, key){
							if(key=='non_field_errors'){
								vm.isValid.cred=true;
								vm.wrnMsg.cred = value[0]
							}
							if(key=='password'){
								vm.isValid.password=true;
								vm.wrnMsg.password = value[0];
							}
							if(key=='username'){
								vm.isValid.username=true;
								vm.wrnMsg.username = value[0];
							}
						})
					}
				}
			};

			utilities.sendRequest(parameters, "no-header");
    	}
    	
    }

})();
