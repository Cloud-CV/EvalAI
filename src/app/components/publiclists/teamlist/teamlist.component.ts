import { Component, OnInit, ViewChildren, QueryList } from '@angular/core';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { Router, ActivatedRoute } from '@angular/router';
import { BehaviorSubject } from 'rxjs';
import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-teamlist',
  templateUrl: './teamlist.component.html',
  styleUrls: ['./teamlist.component.scss']
})
export class TeamlistComponent implements OnInit {

  /**
   * Auth Service public instance
   */
  authServicePublic: any;

  /**
   * Router public instance
   */
  routerPublic: any;

  /**
   * Team list
   */
  allTeams = [];

  /**
   * Filtered team list
   */
  filteredTeams = [];

  /**
   * Filtered team observable-source
   */
  private filteredTeamSource = new BehaviorSubject(this.filteredTeams);

  /**
   * Filtered team observable
   */
  filteredTeamsObservable = this.filteredTeamSource.asObservable();

  /**
   * See more content in frame
   */
  seeMore = 1;

  /**
   * Frame size
   */
  windowSize = 2;

  /**
   * Select team title
   */
  teamSelectTitle = '';

  /**
   * Create team title
   */
  teamCreateTitle = '';

  /**
   * Create team button
   */
  teamCreateButton = '';

  /**
   * Is a host
   */
  isHost = false;

  /**
   * Is router currently on challenges page
   */
  isOnChallengePage = false;

  /**
   * Fetch teams URL
   */
  fetchTeamsPath: any;

  /**
   * Create teams URL
   */
  createTeamsPath: any;

  /**
   * Delete teams URL
   */
  deleteTeamsPath: any;

  /**
   * Currently selected team
   */
  selectedTeam: any = null;

  /**
   * challenge object
   */
  challenge: any;

  /**
   * Form components
   */
  teamForm = 'formteam';

  /**
   * Form fields in the team form (team cards)
   */
  @ViewChildren('formteam')
  components: QueryList<TeamlistComponent>;

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param authService  AuthService Injection.
   * @param apiService  ApiService Injection.
   * @param challengeService  ChallengeService Injection.
   * @param endpointsService  EndpointsService Injection.
   */
  constructor(private apiService: ApiService,
              private authService: AuthService,
              private globalService: GlobalService,
              private router: Router,
              private route: ActivatedRoute,
              private challengeService: ChallengeService,
              private endpointsService: EndpointsService) { }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.authServicePublic = this.authService;
    this.routerPublic = this.router;
    if (this.router.url === '/teams/hosts') {
      this.isHost = true;
      this.fetchTeamsPath = 'hosts/challenge_host_team';
      this.createTeamsPath = 'hosts/create_challenge_host_team';
      this.deleteTeamsPath = 'hosts/remove_self_from_challenge_host';
      this.fetchMyTeams(this.fetchTeamsPath);
      this.teamCreateTitle = 'Create a New Team';
      this.teamSelectTitle = 'Select a Challenge Host Team';
      this.teamCreateButton = 'Create Host Team';
    } else {
      if (this.router.url !== '/teams/participants') {
        this.isOnChallengePage = true;
        this.challengeService.currentChallenge.subscribe(challenge => this.challenge = challenge);
      }
      this.fetchTeamsPath = 'participants/participant_team';
      this.createTeamsPath = this.fetchTeamsPath;
      this.deleteTeamsPath = 'participants/remove_self_from_participant_team';
      this.fetchMyTeams(this.fetchTeamsPath);
      this.teamCreateTitle = 'Create a New Participant Team';
      this.teamSelectTitle = 'My Existing Participant Teams';
      this.teamCreateButton = 'Create Participant Team';
    }
  }

  /**
   * Show more results.
   */
  seeMoreClicked() {
    this.seeMore = this.seeMore + 1;
    this.updateTeamsView(false);
  }

  /**
   * Update teams view (called after fetching teams from API).
   * @param reset  reset flag
   */
  updateTeamsView(reset) {
    if (reset) {
      this.seeMore = 1;
    }
    this.filteredTeams = this.allTeams.slice(0, (this.seeMore * this.windowSize));
    this.filteredTeamSource.next(this.filteredTeams);
  }

  /**
   * Fetch my teams from a given URL.
   * @param path  Fetch teams URL
   */
  fetchMyTeams(path) {
    if (this.authService.isLoggedIn()) {
      this.fetchTeams(path);
    }
  }

  /**
   * Select a team and unselect others.
   */
  selectTeamWrapper() {
    const SELF = this;
    const selectTeam = (team) => {
      SELF.selectedTeam = team;
      SELF.unselectOtherTeams(SELF);
    };
    return selectTeam;
  }

  /**
   * Unselecting other teams function.
   */
  unselectOtherTeams(self) {
    const temp = self.allTeams.slice();
    for (let i = 0; i < temp.length; i++) {
      temp[i]['isSelected'] = false;
      if (self.selectedTeam['id'] === temp[i]['id']) {
        temp[i]['isSelected'] = true;
      }
    }
    self.allTems = temp;
    self.updateTeamsView(false);
  }

  /**
   * Append additional parameters to teams objects.
   */
  appendIsSelected(teams) {
    for (let i = 0; i < teams.length; i++) {
      teams[i]['isSelected'] = false;
      teams[i]['isHost'] = true;
    }
    return teams;
  }

  /**
   * Fetch teams from backend.
   * @param path  Fetch teams URL.
   */
  fetchTeams(path) {
    const SELF = this;
    this.apiService.getUrl(path).subscribe(
      data => {
        if (data['results']) {
          SELF.allTeams = data['results'];
          if (SELF.isHost || SELF.isOnChallengePage) {
            SELF.allTeams = SELF.appendIsSelected(SELF.allTeams);
          }
          SELF.updateTeamsView(true);
        }
      },
      err => {
        SELF.globalService.handleApiError(err, false);
      },
      () => {
        console.log('Teams fetched for teamlist', path, 'on', SELF.routerPublic.url);
      }
    );
  }

  /**
   * Display confirm dialog before deleting a team.
   */
  deleteTeamWrapper() {
    const SELF = this;
    const deleteTeam = (e) => {
      const apiCall = () => {
        SELF.apiService.deleteUrl(SELF.deleteTeamsPath + '/' + e).subscribe(
        data => {
          // Success Message in data.message
          SELF.globalService.showToast('success', 'You were removed from the team!', 5);
          SELF.fetchMyTeams(SELF.fetchTeamsPath);
          SELF.selectedTeam = null;
        },
        err => {
          SELF.globalService.handleApiError(err);
        },
        () => console.log('DELETE-TEAM-FINISHED')
        );
      };
      const PARAMS = {
        title: 'Would you like to remove yourself ?',
        content: 'Note: This action will remove you from the team.',
        confirm: 'Yes',
        deny: 'Cancel',
        confirmCallback: apiCall
      };
      SELF.globalService.showConfirm(PARAMS);
      return false;
    };
    return deleteTeam;
  }

  /**
   * Display Modal for editing team details.
   */
  editTeamWrapper() {
    const SELF = this;
    const editTeam = (team) => {
      const apiCall = (params) => {
        const BODY = JSON.stringify(params);
        SELF.apiService.patchUrl(SELF.endpointsService.participantTeamURL(team), BODY).subscribe(
        data => {
          // Success Message in data.message
          SELF.globalService.showToast('success', 'Team Updated', 5);
          SELF.fetchMyTeams(SELF.fetchTeamsPath);
          SELF.selectedTeam = null;
        },
        err => {
          SELF.globalService.handleApiError(err);
        },
        () => console.log('TEAM-UPDATE-FINISHED')
        );
        console.log('api_call', params, team);
      };
      const PARAMS = {
        title: 'Change Team Name',
        content: 'Enter new team name',
        confirm: 'Confirm',
        deny: 'Cancel',
        form: [
          {
            isRequired: true,
            label: 'team_name',
            placeholder: 'Team Name',
            type: 'text'
          },
          {
            isRequired: false,
            label: 'team_url',
            placeholder: 'Team URL',
            type: 'text'
          }
        ],
        confirmCallback: apiCall
      };
      SELF.globalService.showModal(PARAMS);
    };
    return editTeam;
  }

  /**
   * Display modal to add members to the team.
   */
  addMembersToTeamWrapper() {
    const SELF = this;
    const addMembersToTeam = (team) => {
      const apiCall = (params) => {
        const BODY = JSON.stringify(params);
        let apiPath = SELF.endpointsService.participantTeamInviteURL(team);
        if (SELF.isHost) {
          apiPath = SELF.endpointsService.hostTeamInviteURL(team);
        }
        SELF.apiService.postUrl(apiPath, BODY).subscribe(
        data => {
          // Success Message in data.message
          SELF.globalService.showToast('success', 'User added to the team successfully', 5);
          SELF.fetchMyTeams(SELF.fetchTeamsPath);
          SELF.selectedTeam = null;
        },
        err => {
          SELF.globalService.handleApiError(err, true);
        },
        () => console.log('USER-ADDED-TO-TEAM-FINISHED')
        );
        console.log('api_call', params, team);
      };
      const PARAMS = {
        title: 'Add other members to this Team',
        content: 'Enter the email address of the person',
        confirm: 'ADD',
        deny: 'Cancel',
        form: [
          {
            isRequired: true,
            label: 'email',
            placeholder: 'Email',
            type: 'email'
          }
        ],
        confirmCallback: apiCall
      };
      SELF.globalService.showModal(PARAMS);
    };
    return addMembersToTeam;
  }

  /**
   * Create Team function.
   * @param formname  name of form fields (#).
   */
  createTeam(formname) {
    this.globalService.formValidate(this.components, this.createTeamSubmit, this);
  }

  /**
   * Called after create team form is validated.
   * @param self  context value of this.
   */
  createTeamSubmit(self) {
    const API_PATH = self.createTeamsPath;
    const url = self.globalService.formValueForLabel(self.components, 'team_url');
    let TEAM_BODY: any = {
      team_name: self.globalService.formValueForLabel(self.components, 'team_name')
    };
    if (url) {
      TEAM_BODY['team_url'] = url;
    }
    TEAM_BODY = JSON.stringify(TEAM_BODY);
    self.apiService.postUrl(API_PATH, TEAM_BODY).subscribe(
      data => {
        // Success Message in data.message
        self.globalService.showToast('success', 'Team created successfully!', 5);
        self.fetchMyTeams(self.fetchTeamsPath);
      },
      err => {
        self.globalService.handleFormError(self.components, err);
      },
      () => console.log('CREATE-TEAM-FINISHED')
    );
  }

  /**
   * Create challenge (redirect).
   */
  createChallenge() {
    this.challengeService.changeCurrentHostTeam(this.selectedTeam);
    this.router.navigate(['/challenge-create']);
  }

  /**
   * Participate in the challenge using selected team.
   */
  participateInChallenge() {
    this.challengeService.participateInChallenge(this.challenge['id'], this.selectedTeam['id']);
  }
}
