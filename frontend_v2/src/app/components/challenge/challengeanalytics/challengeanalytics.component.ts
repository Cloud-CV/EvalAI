import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

// import service
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { WindowService } from '../../../services/window.service';
import { ChallengeService } from '../../../services/challenge.service';

@Component({
  selector: 'app-challengeanalytics',
  templateUrl: './challengeanalytics.component.html',
  styleUrls: ['./challengeanalytics.component.scss'],
})
export class ChallengeanalyticsComponent implements OnInit {
  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Challenge Id
   */
  challengeId = null;

  /**
   * Current challenge phase
   */
  currentPhase = [];

  /**
   * Total submissions
   */
  totalSubmission = {};

  /**
   * Total participated teams
   */
  totalParticipatedTeams = {};

  /**
   * Last submission time
   */
  lastSubmissionTime = {};

  /**
   * Total challenge teams
   */
  totalChallengeTeams = [];

  /**
   * Lohin route path
   */
  loginRoutePath = '/auth/login';

  constructor(
    private apiService: ApiService,
    private globalService: GlobalService,
    private endpointService: EndpointsService,
    private challengeService: ChallengeService,
    private router: Router,
    private windowService: WindowService
  ) {}

  ngOnInit() {
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
      this.challengeId = this.challenge['id'];
      if (this.challengeId !== undefined && this.challengeId !== null) {
        this.showChallengeAnalysis();
      }
    });
  }

  errCallBack(err) {
    this.globalService.stopLoader();
    this.globalService.handleApiError(err);
    if (err.status === 403) {
      this.router.navigate(['permission-denied']);
      this.globalService.showToast('error', 'Permission Denied');
    } else if (err.status === 401) {
      this.globalService.showToast('error', 'Timeout, Please login again to continue!');
      this.globalService.resetStorage();
      this.router.navigate([this.loginRoutePath]);
    }
  }

  showChallengeAnalysis() {
    this.globalService.startLoader('');
    let API_PATH = this.endpointService.teamCountAnalyticsURL(this.challengeId);
    this.apiService.getUrl(API_PATH).subscribe(
      (response) => {
        this.globalService.stopLoader();
        this.totalChallengeTeams = response.participant_team_count;
      },
      (err) => {
        this.errCallBack(err);
      },
      () => {}
    );

    this.globalService.startLoader('');
    API_PATH = this.endpointService.challengePhaseURL(this.challengeId);
    this.apiService.getUrl(API_PATH).subscribe(
      (response) => {
        this.globalService.stopLoader();
        this.currentPhase = response.results;
        const challengePhaseId = [];

        for (let phaseCount = 0; phaseCount < this.currentPhase.length; phaseCount++) {
          challengePhaseId.push(this.currentPhase[phaseCount].id);
          const PATH_API = this.endpointService.challengePhaseAnalyticsURL(
            this.challengeId,
            this.currentPhase[phaseCount].id
          );
          this.apiService.getUrl(PATH_API).subscribe(
            (res) => {
              for (let i = 0; i < challengePhaseId.length; i++) {
                if (challengePhaseId[i] === res.challenge_phase) {
                  this.totalSubmission[challengePhaseId[i]] = res.total_submissions;
                  this.totalParticipatedTeams[challengePhaseId[i]] = res.participant_team_count;
                  break;
                }
              }
            },
            (err) => {
              this.errCallBack(err);
            },
            () => {}
          );
        }

        for (let phaseCount = 0; phaseCount < this.currentPhase.length; phaseCount++) {
          const PATH_API = this.endpointService.lastSubmissionAnalyticsURL(
            this.challengeId,
            this.currentPhase[phaseCount].id
          );
          this.apiService.getUrl(PATH_API).subscribe(
            (res) => {
              for (let i = 0; i < challengePhaseId.length; i++) {
                if (challengePhaseId[i] === res.challenge_phase) {
                  const reg = new RegExp('^[0-9]');
                  if (reg.test(res.last_submission_timestamp_in_challenge_phase)) {
                    this.lastSubmissionTime[challengePhaseId[i]] = res.last_submission_timestamp_in_challenge_phase;
                  } else {
                    this.lastSubmissionTime[challengePhaseId[i]] = undefined;
                  }
                  break;
                }
              }
            },
            (err) => {
              this.errCallBack(err);
            },
            () => {}
          );
        }
      },
      (err) => {
        this.errCallBack(err);
      },
      () => {}
    );
  }

  downloadChallengeParticipantTeams() {
    const API_PATH = this.endpointService.downloadParticipantsAnalyticsURL(this.challengeId);
    this.apiService.getUrl(API_PATH, false).subscribe(
      (response) => {
        this.windowService.downloadFile(response, 'participant_teams_' + this.challengeId + '.csv');
      },
      (err) => {
        this.globalService.showToast('error', err.error.error);
      },
      () => {}
    );
  }
}
