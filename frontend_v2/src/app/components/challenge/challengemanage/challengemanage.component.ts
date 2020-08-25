import { Component, OnInit, OnDestroy } from '@angular/core';

// import service
import { EndpointsService } from '../../../services/endpoints.service';
import { AuthService } from '../../../services/auth.service';
import { ChallengeService } from '../../../services/challenge.service';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';

@Component({
  selector: 'app-challengemanage',
  templateUrl: './challengemanage.component.html',
  styleUrls: ['./challengemanage.component.scss'],
})
export class ChallengemanageComponent implements OnInit, OnDestroy {
  /**
   * store worker logs
   */
  workerLogs = [];

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Is user logged in
   */
  isLoggedIn = false;

  /**
   * An interval for fetching the leaderboard data in every 5 seconds
   */
  pollingInterval: any;

  constructor(
    private endpointService: EndpointsService,
    private authService: AuthService,
    private challengeService: ChallengeService,
    private apiService: ApiService,
    private globalService: GlobalService
  ) {}

  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
    });
    this.fetchWorkerLogs();
    this.startLoadingLogs();
  }

  // API call to manage the worker from UI.
  // Response data will be like: {action: "Success" or "Failure", error: <String to include only if action is Failure.>}
  manageWorker(action) {
    const SELF = this;
    const API_PATH = SELF.endpointService.manageWorkerURL(SELF.challenge['id'], action);
    const BODY = JSON.stringify('');
    SELF.apiService.putUrl(API_PATH, BODY).subscribe(
      (data) => {
        if (data[action] === 'Success') {
          SELF.globalService.showToast('success', 'Worker(s) ' + action + 'ed succesfully.', 5);
        } else {
          SELF.globalService.showToast('error', data['error'], 5);
        }
      },
      (err) => {
        SELF.globalService.handleApiError(err, true);
      },
      () => {}
    );
  }

  // Get the logs from worker if submissions are failing.
  fetchWorkerLogs() {
    const API_PATH = this.endpointService.getLogsURL(this.challenge['id']);
    const SELF = this;
    SELF.apiService.getUrl(API_PATH, true, false).subscribe(
      (data) => {
        SELF.workerLogs = [];
        for (let i = 0; i < data.logs.length; i++) {
          SELF.workerLogs.push(data.logs[i]);
        }
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );
  }

  // Get the logs from worker if submissions are failing at an interval of 5sec.
  startLoadingLogs() {
    const SELF = this;
    SELF.pollingInterval = setInterval(function () {
      SELF.fetchWorkerLogs();
    }, 5000);
  }

  ngOnDestroy() {
    clearInterval(this.pollingInterval);
  }
}
