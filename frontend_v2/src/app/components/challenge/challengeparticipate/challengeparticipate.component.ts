import { Component, OnInit, ViewChildren, QueryList } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Router, ActivatedRoute } from '@angular/router';
import { NGXLogger } from 'ngx-logger';
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { ChallengeService } from '../../../services/challenge.service';
import { GlobalService } from '../../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengeparticipate',
  templateUrl: './challengeparticipate.component.html',
  styleUrls: ['./challengeparticipate.component.scss'],
})
export class ChallengeparticipateComponent implements OnInit {
  /**
   * Is user logged in
   */
  isLoggedIn = false;

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Router's public instance
   */
  routerPublic: any;

  /**
   * Is user a participant
   */
  isParticipated: any;

  /**
   * Is challenge active
   */
  isActive: any;

  /**
   * Is currently selected
   */
  isSelected = false;

  /**
   * Team list
   */
  allTeams = [];

  /**
   * Currently selected team
   */
  selectedTeam: any = null;

  /**
   * See more content in frame
   */
  seeMore = 1;

  /**
   * Frame size
   */
  windowSize = 2;

  /**
   * Filtered team list
   */
  filteredTeams = [];

  /**
   * Is name focused
   */
  isnameFocused = false;

  /**
   * Is url focused
   */
  isurlFocused = false;

  /**
   * Is team name required
   */
  isTeamNameRequired = false;

  /**
   * Create team Object
   */
  create_team = {
    team_name: '',
    team_url: '',
  };

  /**
   * Filtered team observable-source
   */
  private filteredTeamSource = new BehaviorSubject(this.filteredTeams);

  /**
   * Filtered team observable
   */
  filteredTeamsObservable = this.filteredTeamSource.asObservable();

  /**
   * Form fields in the team form (team cards)
   */
  @ViewChildren('formteam')
  components: QueryList<ChallengeparticipateComponent>;

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
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param authService  AuthService Injection.
   * @param globalService  GlobalService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(
    private authService: AuthService,
    private apiService: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private challengeService: ChallengeService,
    private globalService: GlobalService,
    private logger: NGXLogger
  ) {}

  /**
   * Component on initialized
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.routerPublic = this.router;
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
      this.isActive = this.challenge['is_active'];
    });
    this.challengeService.currentParticipationStatus.subscribe((status) => {
      this.isParticipated = status;
      if (status) {
        const REDIRECT = this.globalService.getData(this.globalService.redirectStorageKey);
        if (REDIRECT && REDIRECT['path']) {
          this.globalService.deleteData(this.globalService.redirectStorageKey);
          this.router.navigate([REDIRECT['path']]);
        } else {
          this.logger.info('navigating to /submit', status);
          this.router.navigate(['../submit'], { relativeTo: this.route });
        }
      }
    });
    this.fetchTeams();
  }

  /**
   * Fetch teams from backend.
   */
  fetchTeams() {
    const SELF = this;
    const path = 'participants/participant_team';
    SELF.globalService.startLoader('Fetching Teams');
    SELF.apiService.getUrl(path).subscribe(
      (data) => {
        SELF.globalService.stopLoader();
        SELF.allTeams = data['results'];
        this.updateTeamsView(true);
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
   * Select a team toggle.
   */
  selectTeamToggle(team) {
    this.isSelected = !this.isSelected;
    this.selectedTeam = team;
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
   * Participate team function.
   */
  participateInChallenge() {
    const confirmCallback = () => {
      this.challengeService.participateInChallenge(this.challenge['id'], this.selectedTeam['id']);
    };

    let content = '' + '<ol>';
    this.termsAndConditionContent.forEach((item) => {
      content += `<li>${item}</li>`;
    });
    content += '</ol>';

    const PARAMS = {
      title: 'Terms and Conditions',
      content: content,
      confirm: 'Participate',
      deny: 'Cancel',
      label: 'I accept terms and conditions',
      confirmCallback: confirmCallback,
      denyCallback: null,
    };
    this.globalService.showTermsAndConditionsModal(PARAMS);
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
      const API_PATH = 'participants/participant_team';
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
          this.fetchTeams();

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
}
