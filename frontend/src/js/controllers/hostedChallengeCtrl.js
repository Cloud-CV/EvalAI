(function () {
  "use strict";

  angular
    .module("evalai")
    .controller("HostedChallengesCtrl", HostedChallengesCtrl);

  HostedChallengesCtrl.$inject = ["utilities"];

  function HostedChallengesCtrl(utilities) {
    var vm = this;
    var userKey = utilities.getData("userKey");

    utilities.showLoader();
    var gmtOffset = moment().utcOffset();
    var gmtSign = gmtOffset >= 0 ? "+" : "-";
    var gmtHours = Math.abs(Math.floor(gmtOffset / 60));
    var gmtMinutes = Math.abs(gmtOffset % 60);
    var gmtZone =
      "GMT " +
      gmtSign +
      " " +
      gmtHours +
      ":" +
      (gmtMinutes < 10 ? "0" : "") +
      gmtMinutes;

    vm.challengeList = [];
    vm.ongoingChallenges = [];
    vm.upcomingChallenges = [];
    vm.pastChallenges = [];
    vm.challengeCreator = {};

    // Set default tab to 'ongoing'
    vm.currentTab = "ongoing";

    // Function to switch between tabs
    vm.setCurrentTab = function (tabName) {
      vm.currentTab = tabName;
    };

    var parameters = {};
    parameters.url = "hosts/challenge_host_team/";
    parameters.method = "GET";
    parameters.token = userKey;
    parameters.callback = {
      onSuccess: function (response) {
        var host_teams = response["data"]["results"];
        parameters.method = "GET";
        var timezone = moment.tz.guess();
        for (var i = 0; i < host_teams.length; i++) {
          parameters.url =
            "challenges/challenge_host_team/" +
            host_teams[i]["id"] +
            "/challenge";
          parameters.callback = {
            onSuccess: function (response) {
              var data = response.data;
              for (var j = 0; j < data.results.length; j++) {
                var challenge = data.results[j];
                vm.challengeList.push(challenge);

                // Categorize challenges by date
                var id = challenge.id;
                vm.challengeCreator[id] = challenge.creator.id;
                utilities.storeData("challengeCreator", vm.challengeCreator);

                var offset = new Date(challenge.start_date).getTimezoneOffset();
                challenge.time_zone = moment.tz.zone(timezone).abbr(offset);
                challenge.gmt_zone = gmtZone;

                // Sort into appropriate arrays based on date comparison
                var current = new Date();
                var startDate = new Date(challenge.start_date);
                var endDate = new Date(challenge.end_date);

                // Check if it's a future challenge
                if (startDate > current) {
                  if (
                    !vm.upcomingChallenges.some((c) => c.id === challenge.id)
                  ) {
                    vm.upcomingChallenges.push(challenge);
                  }
                }
                // Check if it's an ongoing challenge
                else if (current >= startDate && current <= endDate) {
                  if (
                    !vm.ongoingChallenges.some((c) => c.id === challenge.id)
                  ) {
                    vm.ongoingChallenges.push(challenge);
                  }
                }
                // Otherwise it's a past challenge
                else if (current > endDate) {
                  if (!vm.pastChallenges.some((c) => c.id === challenge.id)) {
                    vm.pastChallenges.push(challenge);
                  }
                }
              }
            },
            onError: function () {
              utilities.hideLoader();
            },
          };
          utilities.sendRequest(parameters);
        }
        utilities.hideLoader();
      },
      onError: function () {
        utilities.hideLoader();
      },
    };
    utilities.sendRequest(parameters);
  }
})();
