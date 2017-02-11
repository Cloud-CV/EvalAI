// Invoking IIFE for profile view

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ProfileCtrl', ProfileCtrl);

    ProfileCtrl.$inject = ['utilities', '$state', '$stateParams'];

    function ProfileCtrl(utilities, $state, $stateParams) {
        var vm = this;

        vm.imgUrlObj = {
            ironman: "dist/images/ironman.png",
            hulk: "dist/images/hulk.png",
            women: "dist/images/women.png",
            bird: "dist/images/bird.png",
            captain: "dist/images/captain.png"
        };

        var hasImage = utilities.getData('avatar');
        if(!hasImage){
            vm.imgUrl = _.sample(vm.imgUrlObj);
            utilities.storeData('avatar', vm.imgUrl);
        }
        else{
            vm.imgUrl = utilities.getData('avatar');
        }
        
        // pich random avatar
        // var imgPath = {
        //     ironman: '../../images/ironman.png';
        // }

        // vm.name = "check"				
    }

})();
