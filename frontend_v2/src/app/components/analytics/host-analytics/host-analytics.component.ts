import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { AuthService } from '../../../services/auth.service';
import { Router } from '@angular/router';
import { WindowService } from '../../../services/window.service';

@Component({
  selector: 'app-host-analytics',
  templateUrl: './host-analytics.component.html',
  styleUrls: ['./host-analytics.component.scss'],
})
export class HostAnalyticsComponent implements OnInit {
  hostTeam = [];
  challengeListCount = 0;
  challengeList = [];
  isTeamSelected = false;
  challengeId = null;
  currentChallengeDetails = {};
  currentPhase = [];
  totalSubmission = {};
  totalParticipatedTeams = {};
  lastSubmissionTime = {};
  totalChallengeTeams = [];
  routePath = '/auth/login';

  constructor(
    private apiService: ApiService,
    private globalService: GlobalService,
    private endpointService: EndpointsService,
    private authService: AuthService,
    private router: Router,
    private windowService: WindowService
  ) {}

  ngOnInit() {
    this.getHostTeam();
    this.getChallengeHost();
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
      this.router.navigate([this.routePath]);
    }
  }

  getHostTeam() {
    this.apiService.getUrl('hosts/challenge_host_team').subscribe(
      (response) => {
        this.hostTeam = response.status === 200 ? [] : response.results;
      },
      (err) => {
        this.globalService.handleApiError(err);
        if (err.status === 403) {
          this.globalService.showToast('error', 'Permission Denied');
        } else if (err.status === 401) {
          this.globalService.showToast('error', 'Timeout, Please login again to continue!');
          this.globalService.resetStorage();
          this.router.navigate([this.routePath]);
        }
      },
      () => {}
    );
  }

  getChallengeHost() {
    this.apiService.getUrl('challenges/challenge?mode=host').subscribe(
      (response) => {
        this.challengeList = response.results;
        this.challengeListCount = this.challengeList.length;
      },
      (err) => {
        this.errCallBack(err);
      },
      () => {}
    );
  }

  showChallengeAnalysis() {
    if (this.challengeId != null) {
      this.isTeamSelected = true;

      this.globalService.startLoader(`Fetching Team count for challenge ${this.challengeId}`);
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

      this.globalService.startLoader(`Fetching phases for challenge ${this.challengeId}`);
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

      for (let i = 0; i < this.challengeList.length; i++) {
        this.challengeList[i]['id'] = String(this.challengeList[i]['id']);
        if (this.challengeList[i]['id'] === this.challengeId) {
          this.currentChallengeDetails = this.challengeList[i];
        }
      }
    } else {
      this.isTeamSelected = false;
    }
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
