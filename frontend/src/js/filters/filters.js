// define filters here

// filter to get ceiling value
(function() {

    'use strict';

    angular
        .module('evalai')
        .filter('ceil', ceil);

    function ceil() {
        return function(input) {
            return Math.ceil(input);
        };
    }

    angular.module('evalai')
        .filter('format_execution_time', format_execution_time);

    function format_execution_time() {
        return function (execution_time) {
            var executiontime = new Date(execution_time * 1000);
            var days = (executiontime.getUTCDate() - 1);
            var hours = executiontime.getUTCHours();
            var minutes = executiontime.getUTCMinutes();
            var seconds = executiontime.getSeconds();
            var timeString = (execution_time != 0) ? (
                (days !=0 ? days.toString().padStart(2, '0') + ' day ' : '') +
                (hours !=0 ? hours.toString().padStart(2, '0') + ' hr ' : '') +
                (minutes != 0 ? minutes.toString().padStart(2, '0') + ' min ' : '') +
                (seconds !=0 ? seconds.toString().padStart(2, '0') + ' sec' : '')
            ) : (seconds.toString().padStart(2, '0') + ' sec');
            return timeString;
        };
    }

    angular.module('evalai')
    .filter('customTitleFilter', customTitleFilter);

    function customTitleFilter() {
        return function(challenges, searchText) {
            if (searchText === undefined) {
                return challenges;
            }
            searchText = searchText.toString().toLowerCase();
            var searchWords = searchText.split(' ');
            return challenges.filter(function(challenge) {
                var title = challenge.title.toLowerCase();
                var tags = challenge.list_tags.join(' ').toLowerCase();
                var domain = challenge.domain ? challenge.domain.toLowerCase() : '';
                var regex = new RegExp("^" + searchWords.join('|'));
                return title.split(' ').some(item => regex.test(item)) || tags.split(' ').some(item => regex.test(item)) || domain.split(' ').some(item => regex.test(item));
            });
        };
    }

    angular.module('evalai')
    .filter('customDomainFilter', customDomainFilter);

    function customDomainFilter() {
        return function(challenges, selecteddomain) {
            selecteddomain = selecteddomain.toString().toLowerCase();
            if (selecteddomain === "all") {
                return challenges;
            }
            else if (selecteddomain === "none") {
                return challenges.filter(function(challenge) {
                    return challenge.domain_name === null;
                });
            }
            return challenges.filter(function(challenge) {
                if (selecteddomain === "") {
                    return true;
                }
                if (challenge.domain_name !== null) {
                    return challenge.domain_name.toLowerCase().indexOf(selecteddomain) !== -1;
                }
                });
        };
    }

})();
