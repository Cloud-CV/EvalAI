import { Component, OnInit, QueryList, ViewChildren, AfterViewInit } from '@angular/core';
import { animate, state, style, transition, trigger } from '@angular/animations';
import { Router, ActivatedRoute } from '@angular/router';
import { NGXLogger } from 'ngx-logger';

// import service
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { WindowService } from '../../../services/window.service';
import { GlobalService } from '../../../services/global.service';
import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { SelectphaseComponent } from '../../utility/selectphase/selectphase.component';
import { environment } from '../../../../environments/environment';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengeviewallsubmissions',
  templateUrl: './challengeviewallsubmissions.component.html',
  styleUrls: ['./challengeviewallsubmissions.component.scss'],
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({ height: '0px', minHeight: '0' })),
      state('expanded', style({ height: '*' })),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
  ],
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
  fileTypes = [{ name: 'csv' }];

  /**
   * Selected file type
   */
  fileSelected = '';

  /**
   * Phase selection type (radio button or select box)
   */
  phaseSelectionType = 'selectBox';

  /**
   * Select box list type
   */
  phaseSelectionListType = 'phase';

  /**
   * Filter query as participant team name
   */
  filterSubmissionsQuery = '';

  /**
   * Fields to be exported
   */
  fieldsToGetExport: any = [];

  /**
   *Check whether team name is filtered
   */
  isTeamFiltered: boolean = true;


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

  columnsToDisplay = [
    's_no',
    'participant_team',
    'created_by',
    'status',
    'execution_time',
    'submitted_file',
    'submission_result_file',
  ];
  columnsHeadings = ['S.No.', 'Team Name', 'Created By', 'Status', 'Execution Time(sec)', 'Submitted File', 'Result File'];

  expandedElement: null;

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
  constructor(
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private challengeService: ChallengeService,
    private globalService: GlobalService,
    private apiService: ApiService,
    private windowService: WindowService,
    private endpointsService: EndpointsService,
    private logger: NGXLogger
  ) {}

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
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
    });
    this.challengeService.currentParticipationStatus.subscribe((status) => {
      this.isParticipated = status;
      if (!status) {
        this.globalService.storeData(this.globalService.redirectStorageKey, { path: this.routerPublic.url });
        let redirectToPath = '';
        if (this.router.url.split('/').length === 4) {
          redirectToPath = '../participate';
        } else if (this.router.url.split('/').length === 5) {
          redirectToPath = '../../participate';
        } else if (this.router.url.split('/').length === 6) {
          redirectToPath = '../../../participate';
        }
        this.router.navigate([redirectToPath], { relativeTo: this.route });
      }
    });
    this.challengeService.currentPhases.subscribe((phases) => {
      this.phases = phases;
      for (let i = 0; i < this.phases.length; i++) {
        if (this.phases[i].is_public === false) {
          this.phases[i].showPrivate = true;
        }
      }
      this.filteredPhases = this.phases;
    });

    this.challengeService.isChallengeHost.subscribe((status) => {
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
    const SELF = this;
    let API_PATH;
    if (SELF.filterSubmissionsQuery === '') {
      API_PATH = SELF.endpointsService.allChallengeSubmissionURL(challenge, phase);
      this.isTeamFiltered = false;
    } else {
      API_PATH = SELF.endpointsService.allChallengeSubmissionWithFilterQueryUrl(
        challenge,
        phase,
        SELF.filterSubmissionsQuery
      );
      this.isTeamFiltered = true;
    }

    let name = SELF.filterSubmissionsQuery;
    SELF.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        if(name == SELF.filterSubmissionsQuery) {
          SELF.submissions = data['results'];
          let index = 0;
          SELF.submissions.forEach((submission) => {
            submission['s_no'] = index + 1;
            index += 1;
          });
          for (let i = 0; i < SELF.submissions.length; i++) {
            // Update view for submission visibility setting
            SELF.submissions[i].submissionVisibilityIcon = SELF.submissions[i].is_public
              ? 'visibility'
              : 'visibility_off';
            SELF.submissions[i].submissionVisibilityText = SELF.submissions[i].is_public ? 'Public' : 'Private';
            // Update view for flag submission setting
            SELF.submissions[i].submissionFlagIcon = SELF.submissions[i].is_flagged ? 'flag' : 'outlined_flag';
            SELF.submissions[i].submissionFlagText = SELF.submissions[i].is_flagged ? 'Flagged' : 'UnFlagged';
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
              if(this.isTeamFiltered) {
                SELF.paginationDetails.currentPage = Math.ceil(data.next.split('page=').join('&').split('&')[1] - 1);
              }
              else {
                SELF.paginationDetails.currentPage = Math.ceil(data.next.split('page=')[1] - 1);
              }
          }
          if (data.previous === null) {
            SELF.paginationDetails.isPrev = 'disabled';
          } else {
            SELF.paginationDetails.isPrev = '';
          }
        }
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        this.logger.info('Fetched submissions', challenge, phase);
      }
    );
  }

  /**
   * Filter submissions by participant team name
   * @param participantTeamName Participant team name
   */
  filterSubmissions(participantTeamName) {
    const SELF = this;
    SELF.filterSubmissionsQuery = participantTeamName;
    SELF.fetchSubmissions(SELF.challenge['id'], SELF.selectedPhase['id']);
  }

  /**
   * Download Submission csv.
   */
  downloadSubmission() {
    if (this.challenge['id'] && this.selectedPhase && this.fileSelected) {
      const API_PATH = this.endpointsService.challengeSubmissionDownloadURL(
        this.challenge['id'],
        this.selectedPhase['id'],
        this.fileSelected
      );
      const SELF = this;
      if (SELF.fieldsToGetExport.length === 0 || SELF.fieldsToGetExport === undefined) {
        SELF.apiService.getUrl(API_PATH, false).subscribe(
          (data) => {
            SELF.windowService.downloadFile(data, 'all_submissions.csv');
          },
          (err) => {
            SELF.globalService.handleApiError(err);
          },
          () => {
            this.logger.info('Download complete.', SELF.challenge['id'], SELF.selectedPhase['id']);
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
        (data) => {
          SELF.submissions = data['results'];
          SELF.paginationDetails.next = data.next;
          SELF.paginationDetails.previous = data.previous;
          // condition for pagination
          if (data.next === null) {
            SELF.paginationDetails.isNext = 'disabled';
            SELF.paginationDetails.currentPage = Math.ceil(data.count / 100);
          } else {
            SELF.paginationDetails.isNext = '';
            if(this.isTeamFiltered) {
              SELF.paginationDetails.currentPage = Math.ceil(data.next.split('page=').join('&').split('&')[1] -1);
            }
            else {
              SELF.paginationDetails.currentPage = Math.ceil(data.next.split('page=')[1] - 1);
            }
          }

          let index =  (SELF.paginationDetails.currentPage-1)*10;
          SELF.submissions.forEach((submission) => {
            submission['s_no'] = index + 1;
            index += 1;
          });

          if (data.previous === null) {
            SELF.paginationDetails.isPrev = 'disabled';
          } else {
            SELF.paginationDetails.isPrev = '';
          }
        },
        (err) => {
          SELF.globalService.handleApiError(err);
        },
        () => {
          this.logger.info('Fetched pagination submissions');
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
   * Update submission flag.
   * @param id  Submission id
   */
  updateSubmissionFlag(id) {
    for (let i = 0; i < this.submissions.length; i++) {
      if (this.submissions[i]['id'] === id) {
        this.submissions[i]['is_flagged'] = !this.submissions[i]['is_flagged'];
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
        this.challenge['id'],
        this.selectedPhase['id'],
        submission.id
      );
      const SELF = this;
      const BODY = JSON.stringify({ is_public: is_public });
      this.apiService.patchUrl(API_PATH, BODY).subscribe(
        () => {
          submission.submissionVisibilityIcon = is_public ? 'visibility' : 'visibility_off';
          submission.submissionVisibilityText = is_public ? 'Public' : 'Private';
          const toastMessage = is_public ? 'The submission is made public' : 'The submission is made private';
          SELF.globalService.showToast('success', toastMessage);
        },
        (err) => {
          SELF.globalService.handleApiError(err);
        },
        () => {}
      );
    }
  }

  /**
   * Change Submission's leaderboard visibility API.
   * @param submission  Selected submission
   * @param is_flagged  is submission flagged boolean field
   */
  toggleSubmissionFlag(submission, is_flagged) {
    is_flagged = !is_flagged;
    const SELF = this;
    SELF.updateSubmissionFlag(submission.id);
    if (SELF.challenge['id'] && SELF.selectedPhase && SELF.selectedPhase['id'] && submission.id) {
      const API_PATH = SELF.endpointsService.challengeSubmissionUpdateURL(
        SELF.challenge['id'],
        SELF.selectedPhase['id'],
        submission.id
      );
      const BODY = JSON.stringify({ is_flagged: is_flagged });
      SELF.apiService.patchUrl(API_PATH, BODY).subscribe(
        () => {
          submission.submissionFlagIcon = is_flagged ? 'flag' : 'outlined_flag';
          submission.submissionFlagText = is_flagged ? 'Flagged' : 'Unflagged';
          const toastMessage = is_flagged ? 'Submission flagged successfully!' : 'Submission unflagged successfully!';
          SELF.globalService.showToast('success', toastMessage);
        },
        (err) => {
          SELF.globalService.handleApiError(err);
        },
        () => {}
      );
    }
  }

  /**
   * Modal to confirm the change of submission flag field
   * @param submission  Selected submission
   * @param is_flagged is submission flagged boolean field
   */
  confirmSubmissionFlagChange(submission, is_flagged) {
    const SELF = this;
    const submissionFlagState = is_flagged ? 'Unflag' : 'Flag';

    SELF.apiCall = () => {
      SELF.toggleSubmissionFlag(submission, is_flagged);
    };

    const PARAMS = {
      title: submissionFlagState + ' this submission ?',
      confirm: "Yes, I'm sure",
      deny: 'No',
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showConfirm(PARAMS);
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
      (data) => {
        if (data['participant_team_submission_count']) {
          SELF.submissionCount = data['participant_team_submission_count'];
        }
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        this.logger.info('Fetched submission counts', challenge, phase);
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
    const submissionVisibilityState = submissionVisibility ? 'private' : 'public';

    SELF.apiCall = () => {
      SELF.changeSubmissionVisibility(submission, submissionVisibility);
    };

    const PARAMS = {
      title: 'Make this submission ' + submissionVisibilityState + '?',
      confirm: "Yes, I'm sure",
      deny: 'No',
      confirmCallback: SELF.apiCall,
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
        (data) => {
          SELF.globalService.showToast('success', data.success, 5);
        },
        (err) => {
          SELF.globalService.handleApiError(err);
        },
        () => {}
      );
    };
    const PARAMS = {
      title: 'Re-run this submission?',
      confirm: "Yes, I'm sure",
      deny: 'No',
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showConfirm(PARAMS);
  }

  /**
   * Delete Submission.
   * @param submission  Submission being deleted
   */
  deleteChallengeSubmission(submission) {
    const SELF = this;
    SELF.apiCall = () => {
      SELF.apiService.deleteUrl(SELF.endpointsService.disableChallengeSubmissionURL(submission.id)).subscribe(
        () => {
          SELF.globalService.showToast('success', 'Submission Deleted successfully', 5);
          SELF.fetchSubmissions(SELF.challenge.id, SELF.selectedPhase.id);
        },
        (err) => {
          SELF.globalService.handleApiError(err, true);
        },
        () => {}
      );
    };
    const PARAMS = {
      title: 'Delete Submission',
      content: 'I understand consequences, delete the submission',
      isButtonDisabled: true,
      confirm: 'Yes',
      deny: 'No',
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }
}
