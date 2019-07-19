import { Component, OnInit, QueryList, ViewChildren, ViewChild, AfterViewInit, Self } from '@angular/core';
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { WindowService } from '../../../services/window.service';
import { GlobalService } from '../../../services/global.service';
import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { Router, ActivatedRoute } from '@angular/router';
import { SelectphaseComponent } from '../../utility/selectphase/selectphase.component';
import { environment } from '../../../../environments/environment.staging';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengeviewallsubmissions',
  templateUrl: './challengeviewallsubmissions.component.html',
  styleUrls: ['./challengeviewallsubmissions.component.scss']
})
export class ChallengeviewallsubmissionsComponent implements OnInit, AfterViewInit {

  /**
   * Phase select card components
   */
  @ViewChildren('phaseselect')
  components: QueryList<SelectphaseComponent>;

  /**
   * Is user logged in
   */
  isLoggedIn = false;

  /**
   * Has view been initialized
   */
  viewInit = false;

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Router's public instance
   */
  routerPublic: any;

  /**
   * User participated
   */
  isParticipated: any;

  /**
   * Is user a challenge host
   */
  isChallengeHost = false;

  /**
   * Submissions list
   */
  submissions = [];

  /**
   * Total submissions
   */
  submissionCount = 0;

  /**
   * Challenge phase list
   */
  phases = [];

  /**
   * Challenge phases filtered
   */
  filteredPhases = [];

  /**
   * Currently selected phase's id
   */
  selectedPhaseId: any;

  /**
   * Currently selected phase
   */
  selectedPhase: any = null;

  /**
   * Is phase selected
   */
  isPhaseSelected = false;

  /**
   * Download file types
   */
  fileTypes = [{ 'name': 'csv' }];

  /**
   * Selected file type
   */
  fileSelected = '';

  /**
   * Phase selection type (radio button or select box)
   */
  phaseSelectionType = 'selectBox';

  /**
   * Fields to be exported
   */
  fieldsToGetExport: any = [];

  /**
   * @param showPagination Is pagination
   * @param paginationMessage Pagination message
   * @param isPrev Previous page state
   * @param isNext Next page state
   * @param currentPage Current Page number
   */
  paginationDetails: any = {};

  /**
   * API call inside the modal
   */
  apiCall: any;

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  GlobalService Injection.
   * @param authService  AuthService Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  Router Injection.
   * @param endpointsService  EndpointsService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private authService: AuthService, private router: Router, private route: ActivatedRoute,
              private challengeService: ChallengeService, private globalService: GlobalService,
              private apiService: ApiService, private windowService: WindowService, private endpointsService: EndpointsService) { }

  /**
   * Component after view initialized.
   */
  ngAfterViewInit() {
    this.viewInit = true;
  }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.routerPublic = this.router;
    this.challengeService.currentChallenge.subscribe(challenge => {
      this.challenge = challenge;
    });
    this.challengeService.currentParticipationStatus.subscribe(status => {
      this.isParticipated = status;
      if (!status) {
        this.globalService.storeData(this.globalService.redirectStorageKey, {path: this.routerPublic.url});
        let redirectToPath = '';
        if (this.router.url.split('/').length === 4) {
          redirectToPath = '../participate';
        } else if (this.router.url.split('/').length === 5) {
          redirectToPath = '../../participate';
        } else if (this.router.url.split('/').length === 6) {
          redirectToPath = '../../../participate';
        }
        this.router.navigate([redirectToPath], {relativeTo: this.route});
      }
    });
    this.challengeService.currentPhases.subscribe(
      phases => {
        this.phases = phases;
        for (let i = 0; i < this.phases.length; i++) {
          if (this.phases[i].is_public === false) {
              this.phases[i].showPrivate = true;
          }
        }
        this.filteredPhases = this.phases;
    });

    this.challengeService.isChallengeHost.subscribe(status => {
      this.isChallengeHost = status;
    });
  }

  /**
   * Called when a phase is selected (from child component)
   */
  phaseSelected() {
    const SELF = this;
    return (phase) => {
      SELF.selectedPhase = phase;
      SELF.isPhaseSelected = true;
      SELF.submissionCount = 0;
      if (SELF.challenge['id'] && phase['id']) {
        SELF.fetchSubmissions(SELF.challenge['id'], phase['id']);
        SELF.fetchSubmissionCounts(this.challenge['id'], phase['id']);
      }
    };
  }

  /**
   * Fetch submissions from API.
   * @param challenge  challenge id
   * @param phase  phase id
   */
  fetchSubmissions(challenge, phase) {
    const API_PATH = this.endpointsService.allChallengeSubmissionURL(challenge, phase);
    const SELF = this;
    this.apiService.getUrl(API_PATH).subscribe(
      data => {
        SELF.submissions = data['results'];
        for (let i = 0; i < SELF.submissions.length; i++) {
          SELF.submissions[i].submissionVisibilityIcon =
            (SELF.submissions[i].is_public) ? 'visibility' : 'visibility_off';
          SELF.submissions[i].submissionVisibilityText =
            (SELF.submissions[i].is_public) ? 'Public' : 'Private';
        }
        SELF.paginationDetails.next = data.next;
        SELF.paginationDetails.previous = data.previous;
        SELF.paginationDetails.totalPage = Math.ceil(data.count / 100);

        if (data.count === 0) {
          SELF.paginationDetails.showPagination = false;
          SELF.paginationDetails.paginationMessage = 'No results found';
        } else {
          SELF.paginationDetails.showPagination = true;
          SELF.paginationDetails.paginationMessage = '';
        }

        // condition for pagination
        if (data.next === null) {
          SELF.paginationDetails.isNext = 'disabled';
          SELF.paginationDetails.currentPage = 1;
        } else {
          SELF.paginationDetails.isNext = '';
          SELF.paginationDetails.currentPage = Math.ceil(data.next.split('page=')[1] - 1);
        }
        if (data.previous === null) {
          SELF.paginationDetails.isPrev = 'disabled';
        } else {
          SELF.paginationDetails.isPrev = '';
        }
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        console.log('Fetched submissions', challenge, phase);
      }
    );
  }

  /**
   * Download Submission csv.
   */
  downloadSubmission() {
    if (this.challenge['id'] && this.selectedPhase && this.fileSelected) {
      const API_PATH = this.endpointsService.challengeSubmissionDownloadURL(
        this.challenge['id'], this.selectedPhase['id'], this.fileSelected
      );
      const SELF = this;
      if (SELF.fieldsToGetExport.length === 0 || SELF.fieldsToGetExport === undefined) {
        SELF.apiService.getUrl(API_PATH, false).subscribe(
          data => {
            SELF.windowService.downloadFile(data, 'all_submissions.csv');
          },
          err => {
            SELF.globalService.handleApiError(err);
          },
          () => {
            console.log('Download complete.', SELF.challenge['id'], SELF.selectedPhase['id']);
          }
        );
      }
    } else {
      if (this.selectedPhase === null) {
        this.globalService.showToast('error', 'Please select a challenge phase!');
      } else if (this.fileSelected === '') {
        this.globalService.showToast('error', 'The file type requested is not valid!');
      }
    }
  }

  /**
   * load data with pagination
   */
  loadPaginationData(url) {
    if (url !== null) {
      const SELF = this;
      const API_PATH = url.split(environment.api_endpoint)[1];

      SELF.apiService.getUrl(API_PATH, true).subscribe(
        data => {
          SELF.submissions = data['results'];
          SELF.paginationDetails.next = data.next;
          SELF.paginationDetails.previous = data.previous;

          // condition for pagination
          if (data.next === null) {
            SELF.paginationDetails.isNext = 'disabled';
            SELF.paginationDetails.currentPage = Math.ceil(data.count / 100);
          } else {
            SELF.paginationDetails.isNext = '';
            SELF.paginationDetails.currentPage = Math.ceil(data.next.split('page=')[1] - 1);
          }

          if (data.previous === null) {
            SELF.paginationDetails.isPrev = 'disabled';
          } else {
            SELF.paginationDetails.isPrev = '';
          }
        },
        err => {
          SELF.globalService.handleApiError(err);
        },
        () => {
          console.log('Fetched pagination submissions');
        }
      );
    }
  }

  /**
   * Update submission's leaderboard visibility.
   * @param id  Submission id
   */
  updateSubmissionVisibility(id) {
    for (let i = 0; i < this.submissions.length; i++) {
      if (this.submissions[i]['id'] === id) {
        this.submissions[i]['is_public'] = !this.submissions[i]['is_public'];
        break;
      }
    }
  }

  /**
   * Change Submission's leaderboard visibility API.
   * @param submission  Selected submission
   * @param is_public  visibility boolean flag
   */
  changeSubmissionVisibility(submission, is_public) {
    is_public = !is_public;
    this.updateSubmissionVisibility(submission.id);
    if (this.challenge['id'] && this.selectedPhase && this.selectedPhase['id'] && submission.id) {
      const API_PATH = this.endpointsService.challengeSubmissionUpdateURL(
        this.challenge['id'], this.selectedPhase['id'], submission.id
      );
      const SELF = this;
      const BODY = JSON.stringify({is_public: is_public});
      this.apiService.patchUrl(API_PATH, BODY).subscribe(
        () => {
          submission.submissionVisibilityIcon = (is_public) ? 'visibility' : 'visibility_off';
          submission.submissionVisibilityText = (is_public) ? 'Public' : 'Private';
          const toastMessage = (is_public) ? 'The submission is made public' : 'The submission is made private';
          SELF.globalService.showToast('success', toastMessage);
        },
        err => {
          SELF.globalService.handleApiError(err);
        },
        () => {}
      );
    }
  }

  /**
   * Fetch number of submissions for a challenge phase.
   * @param challenge  challenge id
   * @param phase  phase id
   */
  fetchSubmissionCounts(challenge, phase) {
    const API_PATH = this.endpointsService.challengeSubmissionCountURL(challenge, phase);
    const SELF = this;
    this.apiService.getUrl(API_PATH).subscribe(
      data => {
        if (data['participant_team_submission_count']) {
          SELF.submissionCount = data['participant_team_submission_count'];
        }
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        console.log('Fetched submission counts', challenge, phase);
      }
    );
  }

  /**
   * Modal to confirm the change of submission visibility
   * @param submission  Selected submission
   * @param submissionVisibility current submission visibility
   */
  confirmSubmissionVisibility(submission, submissionVisibility) {
    const SELF = this;
    let toggleSubmissionVisibilityState;
    (submissionVisibility) ?
    (toggleSubmissionVisibilityState = 'private') :
    (toggleSubmissionVisibilityState = 'public');

    SELF.apiCall = () => {
      SELF.changeSubmissionVisibility(submission, submissionVisibility);
    };

    const PARAMS = {
      title: 'Make this submission ' + toggleSubmissionVisibilityState + '?',
      confirm: 'Yes, I\'m sure',
      deny: 'No',
      confirmCallback: SELF.apiCall
    };
    SELF.globalService.showConfirm(PARAMS);
  }

  /**
   * Modal to confirm the submission re-run
   * @param submissionId submission id
   */
  reRunSubmission(submissionId) {
    const SELF = this;
    const API_PATH = SELF.endpointsService.reRunSubmissionURL(submissionId);
    SELF.apiCall = () => {
      const BODY = {};
      SELF.apiService.postUrl(API_PATH, BODY).subscribe(
        data => {
          SELF.globalService.showToast('success', data.success, 5);
        },
        err => {
          SELF.globalService.handleApiError(err);
        },
        () => {}
      );
    };
    const PARAMS = {
      title: 'Re-run this submission?',
      confirm: 'Yes, I\'m sure',
      deny: 'No',
      confirmCallback: SELF.apiCall
    };
    SELF.globalService.showConfirm(PARAMS);
  }
}
