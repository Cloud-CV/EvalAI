import { Component, OnInit, ViewChildren, QueryList, OnDestroy } from '@angular/core';
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
  styleUrls: ['./teamlist.component.scss'],
})
export class TeamlistComponent implements OnInit, OnDestroy {
  isnameFocused = false;
  isurlFocused = false;
  isTeamNameRequired = false;

  /**
   * Auth Service public instance
   */
  authServicePublic: any;

  /**
   * Router public instance
   */
  routerPublic: any;

  /**
   * Authentication Service subscription
   */
  authServiceSubscription: any;

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
   * Create team Object
   */
  create_team = {
    team_name: '',
    team_url: '',
  };

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
   * Delete member URL
   */
  deleteMembersPath: any;

  /**
   * Currently selected team
   */
  selectedTeam: any = null;

  /**
   * Currently clicked team
   */
  currentlyClickedTeam: any = null;

  /**
   * challenge object
   */
  challenge: any;

  /**
   * To call the API inside the modal
   */
  apiCall: any;

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
   * Routh path for login
   */
  authRoutePath = '/auth/login';

  /**
   * Route path for host teams
   */
  hostTeamRoutePath = '/teams/hosts';

  /**
   * Route path for participant teams
   */
  participantTeamRoutePath = '/teams/participants';

  /**
   * Route path for create challenge
   */
  createChallengeRoutePath = '/challenge-create';
  
  /**
   * Route path for create template challenge page
   */
  createTemplateChallengeRoutePath = '/template-challenge-create';

  /**
   * Filter query as participant team name
   */
  filterTeamsQuery = '';

  /**
   * Content for terms and conditions
   */
  termsAndConditionContent = [
    'Participants can train their models with the released training set' +
      ', also with other training images as long as they are disjoint with the test set' +
      '(see <a class="blue-text" href="https://arxiv.org/pdf/1804.09691.pdf" target="_blank">arXiv paper</a>)',

    'We provide the evaluation codes, along with the released validation dataset, ' +
      'for participants to validate their algorithms on validation set during the <strong>validation phase</strong>.' +
      'The usage instruction is described in "readme.txt" released along with the train/validation data. ',

    'For <strong>testing phase</strong> of <strong>identification</strong> track, ' +
      'we will release the test set where gallery set is fully labelled with idenitities, ' +
      'and probe images with only pseudo labels (not related to identities). ' +
      "Participants will submit a file reporting each probe image's " +
      'feature distance to the top-20 matching gallery identities and the corresponding identity indexes ' +
      '(see "submission format" on the "Overview" page), and then their performance will be measured by our system.   ',

    'For <strong>testing phase</strong> of <strong>verification</strong> track, ' +
      'we will release the images with only pseudo labels and the constructed image pairs, ' +
      'without indicating they are positive or negative. ' +
      "Participants will submit a file reporting each image pair's matching socre, " +
      'and then their performance will be measured by our system.   ',
  ];

  /**
   * Team list route's query parameter subscription
   */
  teamListRouteQueryParamSub = null;

  /**
   * Is the team being selected for a template based challenge or not
   */
  isTemplateChallenge = false;

  /**
   * Id of the challenge template selected
   */
  templateId = null;

  /**
   * Number of phases in the challenge template
   */
  templatePhases = null;

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
  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private globalService: GlobalService,
    private router: Router,
    private route: ActivatedRoute,
    private challengeService: ChallengeService,
    private endpointsService: EndpointsService
  ) {}

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.routerPublic = this.router;

    if (!this.authService.isLoggedIn()) {
      this.router.navigate([this.authRoutePath]);
    }

    this.authServicePublic = this.authService;

    this.authServiceSubscription = this.authService.change.subscribe((authState) => {
      if (!authState.isLoggedIn) {
        this.router.navigate([this.authRoutePath]);
      }
    });

    this.teamListRouteQueryParamSub = this.route
      .queryParams
      .subscribe(params => {
        this.isTemplateChallenge = params['template'] || false;
        if(this.isTemplateChallenge){
          this.templateId = params['templateId'];
          this.templatePhases = params['templatePhases'];
        }
      });

    if (this.router.url === this.hostTeamRoutePath || this.isTemplateChallenge) {
      this.isHost = true;
      this.fetchTeamsPath = 'hosts/challenge_host_team';
      this.createTeamsPath = 'hosts/create_challenge_host_team';
      this.deleteTeamsPath = 'hosts/remove_self_from_challenge_host';
      this.deleteMembersPath = 'hosts/challenge_host_team/<team_id>/challenge_host/';
      this.fetchMyTeams(this.fetchTeamsPath);
      this.teamCreateTitle = 'Create a New Team';
      this.teamSelectTitle = 'Please Select a Challenge Host Team';
      this.teamCreateButton = 'Create Host Team';
    } else {
      if (this.router.url !== this.participantTeamRoutePath) {
        this.isOnChallengePage = true;
        this.challengeService.currentChallenge.subscribe((challenge) => (this.challenge = challenge));
      }
      this.fetchTeamsPath = 'participants/participant_team';
      this.createTeamsPath = this.fetchTeamsPath;
      this.deleteTeamsPath = 'participants/remove_self_from_participant_team';
      this.deleteMembersPath = 'participants/participant_team/<team_id>/participant/';
      this.fetchMyTeams(this.fetchTeamsPath);
      this.teamCreateTitle = 'Create a New Participant Team';
      this.teamSelectTitle = 'My Existing Participant Teams';
      this.teamCreateButton = 'Create Participant Team';
    }
  }

  ngOnDestroy() {
    if (this.authServiceSubscription) {
      this.authServiceSubscription.unsubscribe();
    }
    this.teamListRouteQueryParamSub.unsubscribe();
  }

  /**
   * Show more results.
   */
  seeMoreClicked() {
    this.seeMore = this.seeMore + 1;
    this.updateTeamsView(false);
  }

  /**
   * Show less results.
   */
  seeLessClicked() {
    this.seeMore = this.seeMore - 1;
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
    this.filteredTeams = this.allTeams.slice((this.seeMore - 1) * this.windowSize, this.seeMore * this.windowSize);
    this.filteredTeamSource.next(this.filteredTeams);
  }

  /**
   * Fetch my teams from a given URL.
   * @param path  Fetch teams URL
   */
  fetchMyTeams(path) {
    if (this.authService.isLoggedIn()) {
      if (this.filterTeamsQuery === '') {
        this.fetchTeams(path);
      } else {
        this.filterTeam(this.filterTeamsQuery);
      }
    }
  }

  /**
   * Select a team and unselect others.
   */
  selectTeamWrapper() {
    const SELF = this;
    const selectTeam = (team) => {
      SELF.selectedTeam = team;
    };
    return selectTeam;
  }

  /**
   * Unselect a team.
   */
  deselectTeamWrapper() {
    const SELF = this;
    const selectTeam = (team) => {
      SELF.currentlyClickedTeam = team;
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
      if (self.currentlyClickedTeam['id'] === temp[i]['id']) {
        temp[i]['isSelected'] = true;
      }
    }
    self.allTeams = temp;
    self.updateTeamsView(false);
  }

  /**
   * Append additional parameters to teams objects.
   */
  appendIsSelected(teams) {
    for (let i = 0; i < teams.length; i++) {
      teams[i]['isSelected'] = false;
      teams[i]['isHost'] = this.isHost;
    }
    return teams;
  }

  /**
   * Fetch teams from backend.
   * @param path  Fetch teams URL.
   */
  fetchTeams(path) {
    const SELF = this;
    this.globalService.startLoader('Fetching Teams');
    this.apiService.getUrl(path).subscribe(
      (data) => {
        this.globalService.stopLoader();
        SELF.updateTeamsData(data);
      },
      (err) => {
        if (err.status === 403) {
          this.router.navigate(['permission-denied']);
        }
        this.globalService.stopLoader();
        SELF.globalService.handleApiError(err, false);
      },
      () => {}
    );
  }

  /**
   * Display confirm dialog before deleting a team.
   */
  deleteTeamWrapper() {
    const SELF = this;
    const deleteTeam = (e) => {
      SELF.apiCall = () => {
        SELF.apiService.deleteUrl(SELF.deleteTeamsPath + '/' + e).subscribe(
          (data) => {
            // Success Message in data.message
            SELF.globalService.showToast('success', 'You were removed from the team!', 5);
            SELF.fetchMyTeams(SELF.fetchTeamsPath);
            SELF.selectedTeam = null;
          },
          (err) => {
            SELF.globalService.handleApiError(err);
          },
          () => {}
        );
      };
      const PARAMS = {
        title: 'Would you like to remove yourself ?',
        content: 'Note: This action will remove you from the team',
        confirm: 'Yes',
        deny: 'Cancel',
        confirmCallback: SELF.apiCall,
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
    let TeamUrl;
    const editTeam = (team) => {
      const teamId = team['id'];
      const teamName = team['team_name'];
      const teamUrl = team['team_url'];
      TeamUrl = this.isHost
        ? SELF.endpointsService.hostTeamURL(teamId)
        : SELF.endpointsService.participantTeamURL(teamId);
      SELF.apiCall = (params) => {
        const BODY = JSON.stringify(params);
        SELF.apiService.patchUrl(TeamUrl, BODY).subscribe(
          (data) => {
            // Success Message in data.message
            SELF.globalService.showToast('success', 'Team Updated', 5);
            SELF.fetchMyTeams(SELF.fetchTeamsPath);
            SELF.selectedTeam = null;
          },
          (err) => {
            SELF.globalService.handleApiError(err);
          },
          () => {}
        );
      };
      const PARAMS = {
        title: 'Edit team details',
        content: '',
        confirm: 'Confirm',
        deny: 'Cancel',
        form: [
          {
            isRequired: false,
            label: 'team_name',
            placeholder: 'Team Name',
            value: teamName,
            type: 'text',
          },
          {
            isRequired: false,
            label: 'team_url',
            placeholder: 'Team URL',
            value: teamUrl,
            type: 'text',
          },
        ],
        isButtonDisabled: true,
        confirmCallback: SELF.apiCall,
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
      SELF.apiCall = (params) => {
        const BODY = JSON.stringify(params);
        let apiPath = SELF.endpointsService.participantTeamInviteURL(team);
        if (SELF.isHost) {
          apiPath = SELF.endpointsService.hostTeamInviteURL(team);
        }
        SELF.apiService.postUrl(apiPath, BODY).subscribe(
          (data) => {
            // Success Message in data.message
            SELF.globalService.showToast('success', 'User added to the team successfully', 5);
            SELF.fetchMyTeams(SELF.fetchTeamsPath);
            SELF.selectedTeam = null;
          },
          (err) => {
            SELF.globalService.handleApiError(err, true);
          },
          () => {}
        );
      };
      const PARAMS = {
        title: 'Invite members to the team',
        content: '',
        confirm: 'ADD',
        deny: 'Cancel',
        form: [
          {
            isRequired: true,
            label: 'email',
            placeholder: 'Enter the email address',
            type: 'email',
          },
        ],
        isButtonDisabled: true,
        confirmCallback: SELF.apiCall,
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
   * @param isvalidForm
   */
  createTeamSubmit(isvalidForm) {
    if (isvalidForm) {
      const API_PATH = this.createTeamsPath;
      const url = this.create_team['team_url'];
      let TEAM_BODY: any = {
        team_name: this.create_team['team_name'],
      };
      if (url) {
        TEAM_BODY['team_url'] = url;
      }
      TEAM_BODY = JSON.stringify(TEAM_BODY);
      this.globalService.startLoader('Creating Team');
      this.apiService.postUrl(API_PATH, TEAM_BODY).subscribe(
        (data) => {
          this.globalService.stopLoader();
          // Success Message in data.message
          this.globalService.showToast('success', 'Team created successfully!', 5);
          this.fetchMyTeams(this.fetchTeamsPath);

          // Reset input
          this.create_team = {
            team_url: '',
            team_name: '',
          };

          this.isnameFocused = false;
          this.isurlFocused = false;
          this.isTeamNameRequired = false;
        },
        (err) => {
          this.globalService.stopLoader();
          this.globalService.showToast('error', err.error.team_name, 5);
          this.globalService.handleFormError(this.components, err);
        },
        () => {}
      );
    } else if (this.create_team['team_name'] === '') {
      this.isTeamNameRequired = true;
    }
  }

  /**
   * Create challenge (redirect).
   */
  createChallenge() {
    this.challengeService.changeCurrentHostTeam(this.selectedTeam);
    this.router.navigate([this.createChallengeRoutePath]);
  }

  createChallengeFromTemplate() {
    this.challengeService.changeCurrentHostTeam(this.selectedTeam);
    this.router.navigate([this.createTemplateChallengeRoutePath, this.templateId, this.templatePhases]);
  }

  /**
   * Display confirm dialog before deleting a team member.
   */
  deleteTeamMemberWrapper() {
    const SELF = this;
    const deleteTeamMember = (team) => {
      const deleteUrl = SELF.deleteMembersPath.replace('<team_id>', team.teamId);
      SELF.apiCall = (params) => {
        SELF.apiService.deleteUrl(deleteUrl + team.participantId).subscribe(
          (data) => {
            // Success Message in data.message
            SELF.globalService.showToast('success', 'Member was removed from the team!', 5);
            SELF.fetchMyTeams(SELF.fetchTeamsPath);
            SELF.selectedTeam = null;
          },
          (err) => {
            SELF.globalService.handleApiError(err);
          },
          () => {}
        );
      };
      const PARAMS = {
        title: 'Would you like to remove this member ?',
        content: 'Note: This action will remove this member from the team',
        confirm: 'Yes',
        deny: 'Cancel',
        confirmCallback: SELF.apiCall,
      };
      SELF.globalService.showConfirm(PARAMS);
      return false;
    };
    return deleteTeamMember;
  }

  /**
   * Filter teams by team name
   * @param teamName Participant team name
   */
  filterTeam(teamName) {
    const SELF = this;
    SELF.filterTeamsQuery = teamName;
    let API_PATH;
    if (SELF.isHost) {
      API_PATH = SELF.endpointsService.FilteredHostTeamURL(teamName);
    } else {
      API_PATH = SELF.endpointsService.FilteredParticipantTeamURL(teamName);
    }
    let name = SELF.filterTeamsQuery;
    SELF.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        if(name == SELF.filterTeamsQuery) {
          SELF.updateTeamsData(data);
        }
      },
      (err) => {
        SELF.globalService.handleApiError(err, true);
      },
      () => {}
    );
  }

  /**
   * Update teams data.
   * @param teamsData  Fetched teams data.
   */
  updateTeamsData(teamsData) {
    if (teamsData['results']) {
      this.allTeams = teamsData['results'];
      if (this.isHost || this.isOnChallengePage) {
        this.allTeams = this.appendIsSelected(this.allTeams);
      }
      this.updateTeamsView(true);
    }
  }
}
