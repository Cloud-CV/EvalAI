import { Component, OnInit, QueryList, ViewChildren, Input, AfterViewInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { NGXLogger } from 'ngx-logger';

// import service
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { WindowService } from '../../../services/window.service';
import { GlobalService } from '../../../services/global.service';
import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';

// import component
import { SelectphaseComponent } from '../../utility/selectphase/selectphase.component';
import { InputComponent } from '../../utility/input/input.component';
import { environment } from '../../../../environments/environment';

import { animate, state, style, transition, trigger } from '@angular/animations';
/**
 * Component Class
 */
@Component({
  selector: 'app-challengesubmissions',
  templateUrl: './challengesubmissions.component.html',
  styleUrls: ['./challengesubmissions.component.scss'],
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({ height: '0px', minHeight: '0' })),
      state('expanded', style({ height: '*' })),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
  ],
})
export class ChallengesubmissionsComponent implements OnInit, AfterViewInit {
  /**
   * Phase select card components
   */
  @ViewChildren('phaseselect')
  components: QueryList<SelectphaseComponent>;

  /**
   * Input parameters object
   */
  @Input() params: any;

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
   * Participated team name
   */
  participatedTeamName = '';

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
   * Highlighted submission
   */
  submissionHighlighted: any = null;

  /**
   * Download file types
   */
  fileTypes = [{ name: 'csv' }, { name: 'tsv' }, { name: 'gz' }];

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
   * @param showPagination Is pagination
   * @param paginationMessage Pagination message
   * @param isPrev Previous page state
   * @param isNext Next page state
   * @param currentPage Current Page number
   */
  paginationDetails: any = {};

  /**
   * To call the API inside modal for editing the submission
   */
  apiCall: any;

  columnsToDisplay = [
    's_no',
    'status',
    'execution_time',
    'input_file',
    'submission_result_file',
    'stdout_file',
    'stderr_file',
  ];
  columnsHeadings = ['S.No.', 'Status', 'Execution Time', 'Submission File', 'Result File', 'Stdout File', 'Stderr File'];

  expandedElement: null;

  /**
   * Modal form items
   */
  @ViewChildren('formFilter')
  formComponents: QueryList<InputComponent>;

  /**
   * Constructor.
   * @param authService  AuthService Injection.
   * @param router  Router Injection.
   * @param route  ActivatedRoute Injection.
   * @param challengeService  ChallengeService Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  Router Injection.
   * @param windowService  WindowService Injection.
   * @param endpointsService  EndpointsService Injection.
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
      this.fetchParticipated_team(this.challenge['id']);
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
        } else {
          this.phases[i].showPrivate = false;
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

      // Handle incorrect state change. In some cases phase selected here is not correct one
      let isValidPhase = false;
      for (let phaseIdx in this.phases) {
        if (this.phases[phaseIdx]['id'] == phase['id']) {
          isValidPhase = true;
          break;
        }
      }
      if (SELF.challenge['id'] && phase['id'] && isValidPhase) {
        SELF.fetchSubmissions(SELF.challenge['id'], phase['id']);
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
    API_PATH = SELF.endpointsService.challengeSubmissionURL(challenge, phase);
    SELF.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        SELF.submissionCount = data['count'];
        SELF.submissions = data['results'];
        let index = 0;
        SELF.submissions.forEach((submission) => {
          submission['s_no'] = index + 1;
          index += 1;
        });
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
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        this.logger.info('Fetched submissions', challenge, phase);
      }
    );
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
      this.apiService.getUrl(API_PATH, false).subscribe(
        (data) => {
          SELF.windowService.downloadFile(data, 'all_submissions.csv');
        },
        (err) => {
          SELF.globalService.handleApiError(err);
        },
        () => {
          this.logger.info('Download complete.', this.challenge['id'], this.selectedPhase['id']);
        }
      );
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
  loadPaginationData = function (url) {
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
            SELF.paginationDetails.currentPage = Math.ceil(data.next.split('page=')[1] - 1);
          }

          let index = (SELF.paginationDetails.currentPage - 1) * 100;
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
  };

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
   * @param id  Submission id
   * @param is_public  visibility boolean flag
   */
  changeSubmissionVisibility(id, is_public) {
    is_public = !is_public;
    if (this.challenge['id'] && this.selectedPhase && this.selectedPhase['id'] && id) {
      const SELF = this;
      const API_PATH = this.endpointsService.challengeSubmissionUpdateURL(
        this.challenge['id'],
        this.selectedPhase['id'],
        id
      );
      const BODY = JSON.stringify({ is_public: is_public });
      this.apiService.patchUrl(API_PATH, BODY).subscribe(
        () => {
          this.updateSubmissionVisibility(id);
        },
        (err) => {
          SELF.globalService.handleApiError(err);
        },
        () => {
          this.logger.info('Updated submission visibility', id);
        }
      );
    }
  }

  /**
   * Update baseline status on my submissions tab
   * @param submissionId Submission Id
   */
  updateBaselineStatus(submissionId) {
    for (let i = 0; i < this.submissions.length; i++) {
      if (this.submissions[i]['id'] === submissionId) {
        this.submissions[i]['is_baseline'] = !this.submissions[i]['is_baseline'];
        break;
      }
    }
  }

  /**
   * Change baseline status API
   * @param submissionId Submission Id
   * @param isBaseline baseline boolean flag
   */
  changeBaselineStatus(submissionId, isBaseline) {
    isBaseline = !isBaseline;
    this.updateBaselineStatus(submissionId);
    if (this.challenge['id'] && this.selectedPhase && this.selectedPhase['id'] && submissionId) {
      const API_PATH = this.endpointsService.challengeSubmissionUpdateURL(
        this.challenge['id'],
        this.selectedPhase['id'],
        submissionId
      );
      const SELF = this;
      const BODY = JSON.stringify({
        is_baseline: isBaseline,
      });
      SELF.apiService.patchUrl(API_PATH, BODY).subscribe(
        () => {},
        (err) => {
          SELF.globalService.handleApiError(err);
        },
        () => {
          this.logger.info('Updated submission visibility', submissionId);
        }
      );
    }
  }

  /**
   * Display Edit Submission Modal.
   * @param submission  Submission being edited
   */
  editSubmission(submission) {
    const SELF = this;
    SELF.apiCall = (params) => {
      let BODY = JSON.parse(JSON.stringify(params));
      if (this.selectedPhase.submission_meta_attributes !== null && this.selectedPhase.submission_meta_attributes !== undefined) {
        BODY["submission_metadata"] = [] 
        for (let idx=0; idx < this.selectedPhase.submission_meta_attributes.length; idx++) {
          let metaAttribute = this.selectedPhase.submission_meta_attributes[idx];
          metaAttribute["value"] = BODY[metaAttribute["name"].toLowerCase()];
          BODY["submission_metadata"].push(metaAttribute);
        }
      }
      SELF.apiService
        .patchUrl(
          SELF.endpointsService.challengeSubmissionUpdateURL(
            SELF.challenge.id,
            submission.challenge_phase,
            submission.id
          ),
          BODY
        )
        .subscribe(
          () => {
            // Success Message in data.message
            SELF.globalService.showToast('success', 'Data updated successfully', 5);
            SELF.fetchSubmissions(SELF.challenge.id, SELF.selectedPhase.id);
          },
          (err) => {
            SELF.globalService.handleApiError(err, true);
          },
          () => this.logger.info('SUBMISSION-UPDATE-FINISHED')
        );
    };
    const PARAMS = {
      title: 'Update Submission Details',
      content: '',
      isButtonDisabled: true,
      confirm: 'Submit',
      deny: 'Cancel',
      form: [
        {
          isRequired: false,
          label: 'method_name',
          placeholder: 'Method Name',
          type: 'text',
          value: submission['method_name'],
          icon: 'fa fa-pencil',
        },
        {
          isRequired: false,
          label: 'method_description',
          placeholder: 'Method Description',
          type: 'textarea',
          value: submission['method_description'],
          icon: 'fa fa-pencil',
        },
        {
          isRequired: false,
          label: 'project_url',
          placeholder: 'Project Url',
          type: 'url',
          value: submission['project_url'],
          icon: 'fa fa-pencil',
        },
        {
          isRequired: false,
          label: 'publication_url',
          placeholder: 'Publication Url',
          type: 'url',
          value: submission['publication_url'],
          icon: 'fa fa-pencil',
        },
      ],
      confirmCallback: SELF.apiCall,
    };
    if (this.selectedPhase.submission_meta_attributes !== null && this.selectedPhase.submission_meta_attributes !== undefined) {
      let attributeDict = {};
      for (let i=0; i < this.selectedPhase.submission_meta_attributes.length; i++) {
        let metaAttribute = this.selectedPhase.submission_meta_attributes[i];
        attributeDict[metaAttribute["name"]] = metaAttribute;
      }
      if (submission.submission_metadata !== undefined && submission.submission_metadata !== null) {
        for (let idx=0; idx < submission.submission_metadata.length; idx++) {
          let metaAttribute = submission.submission_metadata[idx];
          let data = {
            isRequired: metaAttribute["required"] == true,
            label: metaAttribute["name"],
            placeholder: metaAttribute["description"],
            type: metaAttribute["type"],
            value: metaAttribute["value"],
            icon: 'fa fa-pencil',
          }
          if (metaAttribute["type"] !== "text") {
            data["attributeOptions"] = attributeDict[metaAttribute["name"]]["options"];
          }
          //TODO: add support for radio button fields
          if (metaAttribute["type"] !== "radio" && metaAttribute["type"] !== "boolean") {
            PARAMS["form"].push(data);
          }
        }
      }
    }
    SELF.globalService.showModal(PARAMS);
  }

  /**
   * Display Cancel Submission Modal.
   * @param submission  Submission being cancelled
   */
   cancelSubmission(submission) {
    const SELF = this;
    if (submission.status != "submitted") {
      SELF.globalService.showToast('error', 'Only unproccessed submissions can be cancelled', 5);
      return;
    }
    SELF.apiCall = () => {
      const BODY = JSON.stringify({
        "status": "cancelled"
      });
      SELF.apiService
        .patchUrl(
          SELF.endpointsService.updateSubmissionMetaURL(
            SELF.challenge.id,
            submission.id
          ),
          BODY
        )
        .subscribe(
          () => {
            // Success Message in data.message
            SELF.globalService.showToast('success', 'Submission status updated successfully', 5);
            SELF.fetchSubmissions(SELF.challenge.id, SELF.selectedPhase.id);
          },
          (err) => {
            SELF.globalService.handleApiError(err, true);
          },
          () => this.logger.info('SUBMISSION-CANCELLED')
        );
    };
    const PARAMS = {
      title: 'Are you sure you want to cancel submission?',
      content: '',
      isButtonDisabled: true,
      confirm: 'Submit',
      deny: 'Cancel',
      form: [],
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }

  /**
   * Get participated team name API
   * @param challengeId Challenge Id
   */
  fetchParticipated_team(challengeId) {
    const SELF = this;
    if (challengeId !== undefined) {
      const API_PATH = SELF.endpointsService.getParticipatedTeamNameURL(challengeId);
      this.apiService.getUrl(API_PATH, true, false).subscribe(
        (data) => {
          SELF.participatedTeamName = data['team_name'];
        },
        (err) => {
          SELF.globalService.handleApiError(err);
        },
        () => {}
      );
    }
  }
}
