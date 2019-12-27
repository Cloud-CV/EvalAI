# Apps : 77.89%
## Utils.py 

## management/commands/seed.py

## apps.py


___

# evalai : 72.22%
## celery.py
## urls.py
```
if settings.DEBUG:
    urlpatterns += [
        url(r"^dbschema/", include("django_spaghetti.urls")),
        url(r"^docs/", include("rest_framework_docs.urls")),
        url(
            r"^api/admin-auth/",
            include("rest_framework.urls", namespace="rest_framework"),
        ),
        url(r"^silk/", include("silk.urls", namespace="silk")),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

```

___

# frontend/src/js/controllers : 78.77%
## analyticsCtrl.js
```
onSuccess: function(response) {
                                        var status = response.status;
                                        var details = response.data;
                                        if (status == 200) {
                                            for(var i=0; i<challengePhaseId.length; i++) {
                                                if (challengePhaseId[i] == details.challenge_phase) {
                                                    vm.totalSubmission[challengePhaseId[i]] = details.total_submissions;
                                                    vm.totalParticipatedTeams[challengePhaseId[i]] = details.participant_team_count;
                                                    i++;
                                                    break;
                                                }
                                            }
                                        }
                                    },

```
```
onSuccess: function(response) {
                                        var status = response.status;
                                        var details = response.data;
                                        if (status == 200) {
                                            for(var i=0; i<challengePhaseId.length; i++) {
                                                if (challengePhaseId[i] == response.data.challenge_phase) {
                                                    vm.lastSubmissionTime[challengePhaseId[i]] = details.last_submission_timestamp_in_challenge_phase;
                                                    i++;
                                                    break;
                                                }
                                            }
                                        }
                                    },
```
```
  vm.downloadChallengeParticipantTeams = function() {
            parameters.url = "analytics/challenges/" + vm.challengeId + "/download_all_participants/";
                parameters.method = "GET";
                parameters.callback = {
                    onSuccess: function(response) {
                        var details = response.data;
                        var anchor = angular.element('<a/>');
                        anchor.attr({
                            href: 'data:attachment/csv;charset=utf-8,' + encodeURI(details),
                            download: 'participant_teams_' + vm.challengeId + '.csv'
                        })[0].click();
                    },
                    onError: function(response) {
                        var details = response.data;
                        $rootScope.notify('error', details.error);
                    }
                };
                utilities.sendRequest(parameters);
        };
```
## authCtrl.js
```
 if (response.status == 201) {
                            vm.isFormError = false;
                            // vm.regMsg = "Registered successfully, Login to continue!";
                            $rootScope.notify("success", "Registered successfully. Please verify your email address!");
                            $state.go('auth.login');
                        }
                        vm.stopLoader();
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.stopLoader();
                            vm.isFormError = true;
                            var non_field_errors, isUsername_valid, isEmail_valid, isPassword1_valid, isPassword2_valid;
                            try {
                                non_field_errors = typeof(response.data.non_field_errors) !== 'undefined' ? true : false;
                                isUsername_valid = typeof(response.data.username) !== 'undefined' ? true : false;
                                isEmail_valid = typeof(response.data.email) !== 'undefined' ? true : false;
                                isPassword1_valid = typeof(response.data.password1) !== 'undefined' ? true : false;
                                isPassword2_valid = typeof(response.data.password2) !== 'undefined' ? true : false;
                                if (non_field_errors) {
                                    vm.FormError = response.data.non_field_errors[0];
                                } else if (isUsername_valid) {
                                    vm.FormError = response.data.username[0];
                                } else if (isEmail_valid) {
                                    vm.FormError = response.data.email[0];
                                } else if (isPassword1_valid) {
                                    vm.FormError = response.data.password1[0];
                                } else if (isPassword2_valid) {
                                    vm.FormError = response.data.password2[0];
                                }
                            } catch (error) {
                                $rootScope.notify("error", error);
                            }
                        }
                        vm.stopLoader();
                    }
```
```
parameters.callback = {
                    onSuccess: function(response) {
                        if (response.status == 200) {
                            utilities.storeData('userKey', response.data.token);
                            if ($rootScope.previousState) {
                                $state.go($rootScope.previousState);
                                vm.stopLoader();
                            } else {
                                $state.go('web.dashboard');
                            }
                        } else {
                            alert("Something went wrong");
                        }
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.isFormError = true;
                            var non_field_errors;
                            try {
                                non_field_errors = typeof(response.data.non_field_errors) !== 'undefined' ? true : false;
                                if (non_field_errors) {
                                    vm.FormError = response.data.non_field_errors[0];
                                }
                            } catch (error) {
                                $rootScope.notify("error", error);
                            }
                        }
                        vm.stopLoader();
                    }
                };
                utilities.sendRequest(parameters, "no-header");
            } else {
                vm.stopLoader();
            }
        };
        // function to check password strength
        vm.checkStrength = function(password) {
            var passwordStrength = utilities.passwordStrength(password);
            vm.message = passwordStrength[0];
            vm.color = passwordStrength[1];
        };

```
```
 password1_valid = typeof(response.data.new_password1) !== 'undefined' ? true : false;
                            password2_valid = typeof(response.data.new_password2) !== 'undefined' ? true : false;
                            if (token_valid) {
                                vm.FormError = "this link has been already used or expired.";
                            } else if (password1_valid) {
                                vm.FormError = Object.values(response.data.new_password1).join(" ");
                            } else if (password2_valid) {
                                vm.FormError = Object.values(response.data.new_password2).join(" ");
                            }
```
## challengeCtrl.js
```
 var elementId = $location.absUrl().split('?')[0].split('#')[1];
                if (elementId) {
                    $anchorScroll.yOffset = 90;
                    $anchorScroll(elementId);
                    $scope.isHighlight = elementId.split("leaderboardrank-")[1];
                }
               
```
```
var newHash = elementId.toString();
            if ($location.hash() !== newHash) {
                $location.hash(elementId);
            } else {
                $anchorScroll();
            }
            $scope.isHighlight = false;
            $anchorScroll.yOffset = 90;
        };
```
```
 var details = response.data;
                                                        vm.existTeam = details;
                                                        // condition for pagination
                                                        if (vm.existTeam.next === null) {
                                                            vm.isNext = 'disabled';
                                                            vm.currentPage = vm.existTeam.count / 10;
                                                        } else {
                                                            vm.isNext = '';
                                                            vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                                        }
                                                        if (vm.existTeam.previous === null) {
                                                            vm.isPrev = 'disabled';
                                                        } else {
                                                            vm.isPrev = '';
                                                        }
                                                        vm.stopLoader();
                                                    });
```
```
var error = response.data;
                                        utilities.storeData('emailError', error.detail);
                                        $state.go('web.permission-denied');
                                        utilities.hideLoader();
                                    }
```
```
 var participationState;
            if (isRegistrationOpen) {
                participationState = 'Close';
            } else {
                participationState = 'Open';
            }
            var confirm = $mdDialog.confirm()
                          .title(participationState + ' participation in the challenge?')
                          .ariaLabel('')
                          .targetEvent(ev)
                          .ok('Yes, I\'m sure')
                          .cancel('No');
            $mdDialog.show(confirm).then(function () {
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge == vm.challengeId) {
                        vm.challengeHostId = challengeHostList[challenge];
                        break;
                    }
                }
                parameters.method = "PATCH";
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.data = {
                    "is_registration_open": !isRegistrationOpen
                };
                parameters.callback = {
                    onSuccess: function() {
                        vm.isRegistrationOpen = !vm.isRegistrationOpen;
                        $rootScope.notify('success', 'Participation is ' + participationState + 'ed successfully');
                    },
                    onError: function(response) {
                        var details = response.data;
                        $rootScope.notify('error', details.error);
                    }
                };
                utilities.sendRequest(parameters);
            }, function() {});
        };

```
```
 var urlRegex = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-/]))?/;
                        var validExtensions = ["json", "zip", "csv"];
                        var isUrlValid = urlRegex.test(vm.fileUrl);
                        var extension = vm.fileUrl.split(".").pop();
                        if (isUrlValid && validExtensions.includes(extension)) {
                            formData.append("file_url", vm.fileUrl);
                        } else {
                            vm.stopLoader();
                            vm.subErrors.msg = "Please enter a valid URL which ends in json, zip or csv file extension!";
                            return false;
```
```
 parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000";
                parameters.method = 'GET';
                parameters.data = {};
                parameters.callback = {
                    onSuccess: function(response) {
                        var details = response.data;
                        if (vm.leaderboard.count !== details.results.count) {
                            vm.showLeaderboardUpdate = true;
                        }
                    },
                    onError: function(response) {
                        var error = response.data;
                        utilities.storeData('emailError', error.detail);
                        $state.go('web.permission-denied');
                        vm.stopLoader();
                    }
                };
                utilities.sendRequest(parameters);
            }, 5000);
        };
```
```
 vm.leaderboard[i]['submission__submitted_at_formatted'] = vm.leaderboard[i]['submission__submitted_at'];
                        vm.initial_ranking[vm.leaderboard[i].id] = i+1;
                        var dateTimeNow = moment(new Date());
                        var submissionTime = moment(vm.leaderboard[i].submission__submitted_at);
                        var duration = moment.duration(dateTimeNow.diff(submissionTime));
                        if (duration._data.years != 0) {
                            var years = duration.asYears();
                            vm.leaderboard[i].submission__submitted_at = years;
                            if (years.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'year';
                            } else {
                                vm.leaderboard[i].timeSpan= 'years';
                            }
                        }
                        else if (duration._data.months !=0) {
                            var months = duration.months();
                            vm.leaderboard[i].submission__submitted_at = months;
                            if (months.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'month';
                            } else {
                                vm.leaderboard[i].timeSpan = 'months';
                            }
                        }
                        else if (duration._data.days !=0) {
                            var days = duration.asDays();
                            vm.leaderboard[i].submission__submitted_at = days;
                            if (days.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'day';
                            } else {
                                vm.leaderboard[i].timeSpan = 'days';
                            }
                        }
                        else if (duration._data.hours !=0) {
                            var hours = duration.asHours();
                            vm.leaderboard[i].submission__submitted_at = hours;
                            if (hours.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'hour';
                            } else {
                                vm.leaderboard[i].timeSpan = 'hours';
                            }                        
                        } 
                        else if (duration._data.minutes !=0) {
                            var minutes = duration.asMinutes();
                            vm.leaderboard[i].submission__submitted_at = minutes;
                            if (minutes.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'minute';
                            } else {
                                vm.leaderboard[i].timeSpan = 'minutes';
                            }
                        }
                        else if (duration._data.seconds != 0) {
                            var second = duration.asSeconds();
                            vm.leaderboard[i].submission__submitted_at = second;
                            if (second.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'second';
                            } else {
                                vm.leaderboard[i].timeSpan = 'seconds';
                            }
```
```
parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/?page=" + Math.ceil(vm.currentPage);
                    parameters.method = 'GET';
                    parameters.data = {};
                    parameters.callback = {
                        onSuccess: function(response) {
                            var details = response.data;
                            // Set the is_public flag corresponding to each submission
                            for (var i = 0; i < details.results.length; i++) {
                                vm.submissionVisibility[details.results[i].id] = details.results[i].is_public;
                                vm.baselineStatus[details.results[i].id] = details.results[i].is_baseline;
                            }
                            if (vm.submissionResult.results.length !== details.results.length) {
                                vm.showUpdate = true;
                            } else {
                                for (i = 0; i < details.results.length; i++) {
                                    if (details.results[i].status !== vm.submissionResult.results[i].status) {
                                        vm.showUpdate = true;
                                        break;
                                    }
                                }
                            }
                        },
                        onError: function(response) {
                            var error = response.data;
                            utilities.storeData('emailError', error.detail);
                            $state.go('web.permission-denied');
                            vm.stopLoader();
                        }
                    };
                    utilities.sendRequest(parameters);
                }, 5000);
            };
```
```
 var details = response.data;
                                vm.submissionResult = details;
                                // condition for pagination
                                if (vm.submissionResult.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.submissionResult.count / 100;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.submissionResult.next.split('page=')[1] - 1);
                                }
                                if (vm.submissionResult.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                                vm.stopLoader();
                            });
                        } else {
                            vm.stopLoader();
                        }
```
```
 submissionObject.classList = ['spin', 'progress-indicator'];
            parameters.url = 'jobs/submissions/' + submissionObject.id + '/re-run/';
            parameters.method = 'POST';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    $rootScope.notify("success", response.data.success);
                    submissionObject.classList = [''];
                },
                onError: function(response) {
                    var error = response.data;
                    $rootScope.notify("error", error);
                    submissionObject.classList = [''];
                }
            };
            utilities.sendRequest(parameters);
        };

```
```
  parameters.url = "challenges/challenge/create/challenge_phase_split/" + vm.phaseSplitId + "/";
            parameters.method = "PATCH";
            parameters.data = {
                "show_leaderboard_by_latest_submission": !vm.selectedPhaseSplit.show_leaderboard_by_latest_submission
            };
            parameters.callback = {
                onSuccess: function (response) {
                    vm.selectedPhaseSplit = response.data;
                    vm.getLeaderboard(vm.selectedPhaseSplit.id);
                    vm.sortLeaderboardTextOption = (vm.selectedPhaseSplit.show_leaderboard_by_latest_submission) ?
                        "Sort by best":"Sort by latest";
                },
                onError: function (response) {
                    var error = response.data;
                    vm.stopLoader();
                    $rootScope.notify("error", error);
                    return false;
                }
            };
            utilities.sendRequest(parameters);
        };
```
```
 vm.startLoader = loaderService.startLoader;
                        vm.startLoader("Loading Submissions");
                        if (url !== null) {
                            //store the header data in a variable
                            var headers = {
                                'Authorization': "Token " + userKey
                            };
                            //Add headers with in your request
                            $http.get(url, { headers: headers }).then(function(response) {
                                // reinitialized data
                                var details = response.data;
                                vm.submissionResult = details;
                                // condition for pagination
                                if (vm.submissionResult.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.submissionResult.count / 100;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.submissionResult.next.split('page=')[1] - 1);
                                }
                                if (vm.submissionResult.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                                vm.stopLoader();
                            });
                        } else {
                            vm.stopLoader();
                        }
```
```
 var status = response.status;
                    var message = "";
                    if(status === 200) {
                      var detail = response.data;
                      if (detail['is_public'] == true) {
                        message = "The submission is made public.";
                      }
                      else {
                        message = "The submission is made private.";
                      }
                      $rootScope.notify("success", message);
                    }
                },
```
```
 if (vm.phaseId) {
                parameters.url = "challenges/" + vm.challengeId + "/phase/" + vm.phaseId + "/download_all_submissions/" + vm.fileSelected + "/";
                if (vm.fieldsToGet === undefined || vm.fieldsToGet.length === 0) {
                    parameters.method = "GET";
                    parameters.callback = {
                        onSuccess: function(response) {
                            var details = response.data;
                            var anchor = angular.element('<a/>');
                            anchor.attr({
                                href: 'data:attachment/csv;charset=utf-8,' + encodeURI(details),
                                download: 'all_submissions.csv'
                            })[0].click();
                        },
                        onError: function(response) {
                            var details = response.data;
                            $rootScope.notify('error', details.error);
                        }
                    };
                    utilities.sendRequest(parameters);
                }
                else {
                    parameters.method = "POST";
                    var fieldsExport = [];
                    for(var i = 0 ; i < vm.fields.length ; i++) {
                        if (vm.fieldsToGet.includes(vm.fields[i].id)) {
                            fieldsExport.push(vm.fields[i].id);
                        }
                    }
                    parameters.data = fieldsExport;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var details = response.data;
                            var anchor = angular.element('<a/>');
                            anchor.attr({
                                href: 'data:attachment/csv;charset=utf-8,' + encodeURI(details),
                                download: 'all_submissions.csv'
                            })[0].click();
                        },
                        onError: function(response) {
                            var details = response.data;
                            $rootScope.notify('error', details.error);
                        }
                    };
                    utilities.sendRequest(parameters);
                }
                
            } else {
                $rootScope.notify("error", "Please select a challenge phase!");
            }
        };
```
```
if (vm.submissionResult.results[i].id === submissionId) {
                    vm.submissionMetaData = vm.submissionResult.results[i];
                    break;
                }
```
```
parameters.url = "challenges/challenge_host_team/" + vm.page.creator.id + "/challenge/" + vm.page.id;
                parameters.method = 'PATCH';
                parameters.data = {
                    "published": !vm.isPublished,
                };
                vm.isPublished = !vm.isPublished;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200) {
                            $mdDialog.hide();
                            $rootScope.notify("success", "The challenge was successfully made " + vm.toggleChallengeState);
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        vm.page.description = vm.tempDesc;
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };
                utilities.sendRequest(parameters);
            }, function() {
            // Nope
            });
        };
        // Edit Challenge Start and End Date
        vm.challengeDateDialog = function(ev) {
            vm.challengeStartDate = moment(vm.page.start_date);
            vm.challengeEndDate = moment(vm.page.end_date);
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-date.html',
                escapeToClose: false
            });
        };
        vm.editChallengeDate = function(editChallengeDateForm) {
            if (editChallengeDateForm) {
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge == vm.challengeId) {
                        vm.challengeHostId = challengeHostList[challenge];
                        break;
                    }
                }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                if (new Date(vm.challengeStartDate).valueOf() < new Date(vm.challengeEndDate).valueOf()) {
                    parameters.data = {
                        "start_date": vm.challengeStartDate,
                        "end_date": vm.challengeEndDate
                    };
                    parameters.callback = {
                        onSuccess: function(response) {
                            var status = response.status;
                            utilities.hideLoader();
                            if (status === 200) {
                                vm.page.start_date = vm.challengeStartDate.format("MMM D, YYYY h:mm:ss A");
                                vm.page.end_date = vm.challengeEndDate.format("MMM D, YYYY h:mm:ss A");
                                $mdDialog.hide();
                                $rootScope.notify("success", "The challenge start and end date is successfully updated!");
                            }
                        },
                        onError: function(response) {
                            utilities.hideLoader();
                            $mdDialog.hide();
                            var error = response.data;
                            $rootScope.notify("error", error);
                        }
                    };
                    utilities.showLoader();
                    utilities.sendRequest(parameters);
                } else {
                    $rootScope.notify("error", "The challenge start date cannot be same or greater than end date.");
                }
            } else {
                $mdDialog.hide();
            }
        };
        $scope.$on('$destroy', function() {
            vm.stopFetchingSubmissions();
            vm.stopLeaderboard();
        });
        $rootScope.$on('$stateChangeStart', function() {
            vm.phase = {};
            vm.isResult = false;
            vm.stopFetchingSubmissions();
            vm.stopLeaderboard();
        });
```
```
 if (acceptTermsAndConditionsForm) {
                if (vm.termsAndConditions) {
                    vm.selectExistTeam();
                    $mdDialog.hide();
                }
            } else {
                $mdDialog.hide();
            }
        };
        
    }

```
## challengeHostTeamsCtrl.js
```
 var details = response.data;
                                vm.existTeam = details;
                                // condition for pagination
                                if (vm.existTeam.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.existTeam.count / 100;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                }
                                if (vm.existTeam.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                                vm.stopLoader();
                            });
                        } else {
                            vm.stopLoader();
                        }
```

```
 vm.startLoader();
                var parameters = {};
                parameters.url = 'hosts/remove_self_from_challenge_host/' + hostTeamId;
                parameters.method = 'DELETE';
                parameters.data = {};
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {
                        vm.team.error = false;
                        $rootScope.notify("info", "You have removed yourself successfully");
                        var parameters = {};
                        parameters.url = 'hosts/challenge_host_team/';
                        parameters.method = 'GET';
                        parameters.token = userKey;
                        parameters.callback = {
                            onSuccess: function(response) {
                                var status = response.status;
                                var details = response.data;
                                if (status == 200) {
                                    vm.existTeam = details;
                                    // condition for pagination
                                    if (vm.existTeam.next === null) {
                                        vm.isNext = 'disabled';
                                        vm.currentPage = vm.existTeam.count / 10;
                                    } else {
                                        vm.isNext = '';
                                        vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                    }
                                    if (vm.existTeam.previous === null) {
                                        vm.isPrev = 'disabled';
                                    } else {
                                        vm.isPrev = '';
                                    }
                                    if (vm.existTeam.count === 0) {
                                        vm.showPagination = false;
                                        vm.paginationMsg = "No team exists for now, start by creating a new team!";
                                    } else {
                                        vm.showPagination = true;
                                        vm.paginationMsg = "";
                                    }
                                }
                                vm.stopLoader();
                            }
                        };
                        utilities.sendRequest(parameters);
                    },
                    onError: function() {
                        vm.stopLoader();
                        $rootScope.notify("error", "Couldn't remove you from the challenge");
                    }
                };
                utilities.sendRequest(parameters);
            }, function() {});
        };
```
```
 var parameters = {};
                parameters.url = 'hosts/challenge_host_teams/' + hostTeamId + '/invite';
                parameters.method = 'POST';
                parameters.data = {
                    "email": result
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {
                        $rootScope.notify("success", parameters.data.email + " has been added successfully");
                    },
                    onError: function(response) {
                        var error = response.data.error;
                        $rootScope.notify("error", error);
                    }
                };
                utilities.sendRequest(parameters);
            });
        };
```
## featuredChallengeCtrl.js
```
var dateTimeNow = moment(new Date());
                        var submissionTime = moment(vm.leaderboard[i].submission__submitted_at);
                        var duration = moment.duration(dateTimeNow.diff(submissionTime));
                        if (duration._data.years != 0) {
                            var years = duration.asYears();
                            vm.leaderboard[i].submission__submitted_at = years;
                            if (years.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'year';
                            } else {
                                vm.leaderboard[i].timeSpan= 'years';
                            }
                        }
                        else if (duration._data.months !=0) {
                            var months = duration.months();
                            vm.leaderboard[i].submission__submitted_at = months;
                            if (months.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'month';
                            } else {
                                vm.leaderboard[i].timeSpan = 'months';
                            }
                        }
                        else if (duration._data.days !=0) {
                            var days = duration.asDays();
                            vm.leaderboard[i].submission__submitted_at = days;
                            if (days.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'day';
                            } else {
                                vm.leaderboard[i].timeSpan = 'days';
                            }
                        }
                        else if (duration._data.hours !=0) {
                            var hours = duration.asHours();
                            vm.leaderboard[i].submission__submitted_at = hours;
                            if (hours.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'hour';
                            } else {
                                vm.leaderboard[i].timeSpan = 'hours';
                            }                        
                        } 
                        else if (duration._data.minutes !=0) {
                            var minutes = duration.asMinutes();
                            vm.leaderboard[i].submission__submitted_at = minutes;
                            if (minutes.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'minute';
                            } else {
                                vm.leaderboard[i].timeSpan = 'minutes';
                            }
                        }
                        else if (duration._data.seconds != 0) {
                            var second = duration.asSeconds();
                            vm.leaderboard[i].submission__submitted_at = second;
                            if (second.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'second';
                            } else {
                                vm.leaderboard[i].timeSpan = 'seconds';
                            }
                        }
                    }
```
## teamsCtrl.js
```
 var details = response.data;
                                vm.existTeam = details;
                                // condition for pagination
                                if (vm.existTeam.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.existTeam.count / 100;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                }
                                if (vm.existTeam.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                                vm.stopLoader();
                            });
                        } else {
                            vm.stopLoader();
                        }
                    };

```
```
$mdDialog.show(confirm).then(function() {
                vm.startLoader();
                var parameters = {};
                parameters.url = 'participants/remove_self_from_participant_team/' + participantTeamId;
                parameters.method = 'DELETE';
                parameters.data = {};
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {
                        vm.team.error = false;
                        $rootScope.notify("info", "You have removed yourself successfully");
                        var parameters = {};
                        parameters.url = 'participants/participant_team';
                        parameters.method = 'GET';
                        parameters.token = userKey;
                        parameters.callback = {
                            onSuccess: function(response) {
                                var status = response.status;
                                var details = response.data;
                                if (status == 200) {
                                    vm.existTeam = details;
                                    // condition for pagination
                                    if (vm.existTeam.next === null) {
                                        vm.isNext = 'disabled';
                                        vm.currentPage = vm.existTeam.count / 10;
                                    } else {
                                        vm.isNext = '';
                                        vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                    }
                                    if (vm.existTeam.previous === null) {
                                        vm.isPrev = 'disabled';
                                    } else {
                                        vm.isPrev = '';
                                    }
                                    if (vm.existTeam.count === 0) {
                                        vm.showPagination = false;
                                        vm.paginationMsg = "No team exists for now. Start by creating a new team!";
                                    } else {
                                        vm.showPagination = true;
                                        vm.paginationMsg = "";
                                    }
                                }
                                vm.stopLoader();
                            }
                        };
                        utilities.sendRequest(parameters);
                    },
                    onError: function(response) {
                        var error = response.data['error'];
                        vm.stopLoader();
                        $rootScope.notify("error", error);
                    }
                };
                utilities.sendRequest(parameters);
            }, function() {
            });
        };
```
```
var parameters = {};
                parameters.url = 'participants/participant_team/' + participantTeamId + '/invite';
                parameters.method = 'POST';
                parameters.data = {
                    "email": result
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var message = response.data['message'];
                        $rootScope.notify("success", message);
                    },
                    onError: function(response) {
                        var error = response.data['error'];
                        $rootScope.notify("error", error);
                    }
                };
                utilities.sendRequest(parameters);
            }, function() {
            });
```
___

#  scripts/workers : 42.96%
## remote_submission_worker.py
## submission_worker.py
## worker_util.py
## rl_submission_worker.py

___

# manage.py : 0%
