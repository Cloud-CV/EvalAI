import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { NGXLogger } from 'ngx-logger';

// import service
import { ApiService } from './api.service';
import { GlobalService } from './global.service';
import { AuthService } from './auth.service';
import { EndpointsService } from './endpoints.service';

@Injectable()
export class ChallengeService {
  private defaultChallenge: any = { 'creator': {}};
  private defaultStars: any = { 'count': 0, 'is_starred': false};
  private defaultPublishChallenge: any = {
    'state': 'Not Published',
    'icon': 'fa fa-eye-slash red-text'
  };
  private isLoggedIn = false;
  private challengeSource = new BehaviorSubject(this.defaultChallenge);
  currentChallenge = this.challengeSource.asObservable();
  private starSource = new BehaviorSubject(this.defaultStars);
  currentStars = this.starSource.asObservable();
  private teamsSource = new BehaviorSubject([]);
  currentParticipantTeams = this.teamsSource.asObservable();
  private phasesSource = new BehaviorSubject([]);
  currentPhases = this.phasesSource.asObservable();
  private phaseSplitSource = new BehaviorSubject([]);
  currentPhaseSplit = this.phaseSplitSource.asObservable();
  private challengeParticipationSource = new BehaviorSubject(false);
  currentParticipationStatus = this.challengeParticipationSource.asObservable();
  private hostTeamSource = new BehaviorSubject(null);
  currentHostTeam = this.hostTeamSource.asObservable();
  private challengeHostSource = new BehaviorSubject(false);
  isChallengeHost = this.challengeHostSource.asObservable();
  private challengePublishSource = new BehaviorSubject(this.defaultPublishChallenge);
  currentChallengePublishState = this.challengePublishSource.asObservable();

  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param authService  AuthService Injection.
   */
  constructor(private apiService: ApiService, private globalService: GlobalService,
              private authService: AuthService, private endpointsService: EndpointsService,
              private logger: NGXLogger) { }

  /**
   * Update current Challenge.
   * @param challenge  new Current-Challenge.
   */
  changeCurrentChallenge(challenge: object) {
    this.challengeSource.next(challenge);
  }

  /**
   * Update user's challenge host status for current challenge.
   * @param isChallengeHost  new challenge host status.
   */
  changeChallengeHostStatus(isChallengeHost: any) {
    this.challengeHostSource.next(isChallengeHost);
  }

  /**
   * Update challenge publish state and icon for current challenge.
   * @param publishChallenge  new challenge publish status and icon.
   */
  changeChallengePublish(publishChallenge: any) {
    this.challengePublishSource.next(publishChallenge);
  }

  /**
   * Update stars for current challenge.
   * @param stars  new stars.
   */
  changeCurrentStars(stars: object) {
    this.starSource.next(stars);
  }

  /**
   * Update current Participant teams.
   * @param teams  new teams.
   */
  changeCurrentParticipantTeams(teams: any) {
    this.teamsSource.next(teams);
  }

  /**
   * Update current Phases for the current challenge.
   * @param phases  new phases.
   */
  changeCurrentPhases(phases: any) {
    this.phasesSource.next(phases);
  }

  /**
   * Update user's participation status for current Challenge.
   * @param participationStatus  new participation status.
   */
  changeParticipationStatus(participationStatus: any) {
    this.challengeParticipationSource.next(participationStatus);
  }

  /**
   * Update current phase splits.
   * @param phaseSplits  new phase splits.
   */
  changeCurrentPhaseSplit(phaseSplits: any) {
    this.phaseSplitSource.next(phaseSplits);
  }

  /**
   * Update current Host Team.
   * @param hostTeam  new host team.
   */
  changeCurrentHostTeam(hostTeam: any) {
    this.hostTeamSource.next(hostTeam);
  }

  /**
   * Fetch challenge details. (internally calls fetchStars, fetchParticipantTeams, fetchPhases, fetchPhaseSplits)
   * @param id  id of new challenge.
   */
  fetchChallenge(id) {
    const API_PATH = this.endpointsService.challengeDetailsURL(id);
    const SELF = this;
    this.changeCurrentPhases([]);
    this.changeCurrentPhaseSplit([]);
    this.authService.change.subscribe((authState) => {
      if (authState['isLoggedIn']) {
        SELF.isLoggedIn = true;
        SELF.fetchStars(id);
        SELF.fetchParticipantTeams(id);
      } else if (!authState['isLoggedIn']) {
        SELF.isLoggedIn = false;
        SELF.changeParticipationStatus(false);
      }
    });
    SELF.fetchPhases(id);
    SELF.fetchPhaseSplits(id);
    SELF.changeChallengeHostStatus(false);
    this.apiService.getUrl(API_PATH).subscribe(
      data => {
        if (data['id'] === parseInt(id, 10)) {
          SELF.changeCurrentChallenge(data);
        }
        const challengePublish = {
          state: '',
          icon: ''
        };
        if (data['published']) {
          challengePublish.state = 'Published';
          challengePublish.icon = 'fa fa-eye green-text';
        } else {
          challengePublish.state = 'Not Published';
          challengePublish.icon = 'fa fa-eye-slash red-text';
        }
        this.changeChallengePublish(challengePublish);
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        this.logger.info('Challenge', id, 'fetched!');
    });
  }

  /**
   * Fetch Stars
   * @param hostTeam  new host team.
   */
  fetchStars(id, callback = null) {
    const API_PATH = this.endpointsService.challengeStarsURL(id);
    const SELF = this;
    this.apiService.getUrl(API_PATH).subscribe(
      data => {
        if (callback) {
          callback(data);
        } else {
          SELF.changeCurrentStars(data);
        }
      },
      err => {
        SELF.globalService.handleApiError(err, false);
      },
      () => {
        this.logger.info('Stars', id, 'fetched!');
      }
    );
  }

  /**
   * Update Stars for a particular challenge
   * @param id  ID of the challenge to be updated
   * @param callback  callback function.
   * @param self  context this
   */
  starToggle(id, callback = null, self = null) {
    const API_PATH = this.endpointsService.challengeStarsURL(id);
    const SELF = this;
    const BODY = JSON.stringify({});
    this.apiService.postUrl(API_PATH, BODY).subscribe(
      data => {
        if (callback) {
          callback(data, self);
        } else {
          SELF.changeCurrentStars(data);
        }
      },
      err => {
        SELF.globalService.handleApiError(err, false);
      },
      () => {
        this.logger.info('Stars', id, 'fetched!');
      }
    );
  }

  /**
   * Load Javascript function.
   * @param url  Name of script.
   * @param implementationCode  callback function.
   * @param location  where to append the file
   * @param env  `This` variable of the environment
   */
  private fetchParticipantTeams(id) {
    const API_PATH = this.endpointsService.challengeParticipantTeamsURL(id);
    const SELF = this;
    this.apiService.getUrl(API_PATH).subscribe(
      data => {
        let teams = [];
        let participated = false;
        if (data['is_challenge_host']) {
          SELF.changeChallengeHostStatus(true);
        }
        if (data['challenge_participant_team_list']) {
          teams = data['challenge_participant_team_list'];
          this.changeCurrentParticipantTeams(teams);
          for (let i = 0; i < teams['length']; i++) {
            if (teams[i]['challenge'] !== null && teams[i]['challenge']['id'] === parseInt(id, 10)) {
              SELF.changeParticipationStatus(true);
              participated = true;
              break;
            }
          }
        }
        if (teams.length === 0 || !participated) {
          SELF.changeParticipationStatus(false);
        }
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        this.logger.info('Participant Teams fetched');
    });
  }


  /**
   * Fetch Phases
   * @param id  id of the challenge.
   */
  private fetchPhases(id) {
    const API_PATH = this.endpointsService.challengePhaseURL(id);
    const SELF = this;
    this.apiService.getUrl(API_PATH).subscribe(
      data => {
        let phases = [];
        if (data['results']) {
          phases = data['results'];
          this.changeCurrentPhases(phases);
        }
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        this.logger.info('Phases fetched');
    });
  }

  /**
   * Fetch Phase Splits
   * @param id  id of the challenge
   */
  private fetchPhaseSplits(id) {
    const API_PATH = this.endpointsService.challengePhaseSplitURL(id);
    const SELF = this;
    this.apiService.getUrl(API_PATH).subscribe(
      data => {
        let phaseSplits = [];
        if (data && data.length > 0) {
          phaseSplits = data;
          this.changeCurrentPhaseSplit(phaseSplits);
        }
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        this.logger.info('Phase Splits fetched');
    });
  }

  /**
   * Participate in challenge with a team
   * @param id  id of the challenge.
   * @param team  team id of the participating team.
   */
  participateInChallenge(id, team) {
    const API_PATH = this.endpointsService.challengeParticipateURL(id, team);
    const SELF = this;
    const BODY = JSON.stringify({});
    this.apiService.postUrl(API_PATH, BODY).subscribe(
      data => {
        SELF.fetchParticipantTeams(id);
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        this.logger.info('Challenge participated');
    });
  }

  /**
   * Make a Challenge submission
   * @param challenge  id of challenge.
   * @param phase  challenge phase id.
   * @param formData  Form Data for submission (file)
   * @param callback callback function
   */
  challengeSubmission(challenge, phase, formData, callback = () => {}) {
    const API_PATH = this.endpointsService.challengeSubmissionURL(challenge, phase);
    const SELF = this;
    this.apiService.postFileUrl(API_PATH, formData).subscribe(
      data => {
        SELF.globalService.showToast('success', 'Submission successful!');
        callback();
      },
      err => {
        SELF.globalService.handleApiError(err);
        callback();
      },
      () => {
        this.logger.info('Submission Uploaded');
    });
  }

  /**
   * Create a new Challenge (Zip Upload)
   * @param hostTeam  Id of hosting team.
   * @param formData  challenge submission data (file)
   * @param callback  callback function
   */
  challengeCreate(hostTeam, formData, callback = () => {}) {
    const API_PATH = this.endpointsService.challengeCreateURL(hostTeam);
    return  this.apiService.postFileUrl(API_PATH, formData);
  }


}
