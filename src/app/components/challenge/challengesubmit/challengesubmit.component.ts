import { Component, OnInit, QueryList, ViewChildren } from '@angular/core';
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { ChallengeService } from '../../../services/challenge.service';
import { Router, ActivatedRoute } from '@angular/router';
import { EndpointsService } from '../../../services/endpoints.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengesubmit',
  templateUrl: './challengesubmit.component.html',
  styleUrls: ['./challengesubmit.component.scss']
})
export class ChallengesubmitComponent implements OnInit {

  /**
   * Is user logged in
   */
  isLoggedIn = false;

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Is challenge host
   */
  isChallengeHost: any;

  /**
   * Router public instance
   */
  routerPublic: any;

  /**
   * Is user a participant
   */
  isParticipated: any;

  /**
   * Is challenge currently active
   */
  isActive: any;

  /**
   * Submission input file
   */
  inputFile = true;

  /**
   * Disable submit button
   */
  disableSubmit = true;

  /**
   * Submission error
   */
  submissionError = '';

  /**
   * Guidelines text
   */
  submissionGuidelines = '';

  /**
   * Form fields name
   */
  submitForm = 'formsubmit';

  /**
   * Challenge phases list
   */
  phases = [];

  /**
   * Filtered challenge phases
   */
  filteredPhases = [];

  /**
   * Selected phase object
   */
  selectedPhase = null;

  /**
   * Phase selection type (radio button or select box)
   */
  phaseSelectionType = 'radioButton';

  /**
   * Api call inside the modal to edit the submission guidelines
   */
  apiCall: any;

  /**
   * Submissions remaining for the selected phase
   */
  selectedPhaseSubmissions = {
    showSubmissionDetails: false,
    remainingSubmissions: {},
    maxExceeded: false,
    maxExceededMessage: '',
    message: ''
  };

  /**
   * Component Class
   */
  @ViewChildren('formsubmit')
  components: QueryList<ChallengesubmitComponent>;

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param authService  AuthService Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private authService: AuthService, private router: Router, private route: ActivatedRoute,
              private challengeService: ChallengeService, private globalService: GlobalService, private apiService: ApiService,
              private endpointsService: EndpointsService) { }

  /**
   * Component on intialization.
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.routerPublic = this.router;
    this.challengeService.currentChallenge.subscribe(challenge => {
      this.challenge = challenge;
      this.isActive = this.challenge['is_active'];
      this.submissionGuidelines = this.challenge['submission_guidelines'];
    });
    this.challengeService.currentParticipationStatus.subscribe(status => {
      this.isParticipated = status;
      if (!status) {
        this.router.navigate(['../participate'], {relativeTo: this.route});
      }
    });
    this.challengeService.currentPhases.subscribe(
      phases => {
        this.phases = phases;
        this.filteredPhases = this.phases.filter(phase => phase['is_active'] === true);
        for (let j = 0; j < this.phases.length; j++) {
          if (phases[j].is_public === false) {
            this.phases[j].showPrivate = true;
          }
        }
    });

    this.challengeService.isChallengeHost.subscribe(status => {
      this.isChallengeHost = status;
    });
  }

  /**
   * Fetch remaining submissions for a challenge phase.
   * @param challenge  challenge id
   * @param phase  phase id
   */
  fetchRemainingSubmissions(challenge, phase) {
    const API_PATH = this.endpointsService.challengeSubmissionsRemainingURL(challenge);
    const SELF = this;
    this.apiService.getUrl(API_PATH).subscribe(
      data => {
        let phaseDetails;
        for (let i = 0; i < data.phases.length; i++) {
          if (data.phases[i].id === phase) {
            phaseDetails = data.phases[i].limits;
            break;
          }
        }
        if (phaseDetails.submission_limit_exceeded) {
          this.selectedPhaseSubmissions.maxExceeded = true;
          this.selectedPhaseSubmissions.maxExceededMessage = phaseDetails.message;
          this.disableSubmit = true;
        } else if (phaseDetails.remaining_submissions_today_count > 0) {
          this.selectedPhaseSubmissions.remainingSubmissions = phaseDetails;
          this.selectedPhaseSubmissions.showSubmissionDetails = true;
          this.disableSubmit = false;
        } else {
          this.selectedPhaseSubmissions.message = phaseDetails;
          this.disableSubmit = true;
        }
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        console.log('Remaining submissions fetched for challenge-phase', challenge, phase);
      }
    );
  }

  /**
   * Called when a phase is selected (from child components)
   */
  phaseSelected() {
    const SELF = this;
    return (phase) => {
      SELF.selectedPhase = phase;
      if (SELF.challenge['id'] && phase['id']) {
        SELF.fetchRemainingSubmissions(SELF.challenge['id'], phase['id']);
      }
    };
  }

  /**
   * Form validate function
   */
  formValidate() {
    if (this.selectedPhaseSubmissions.remainingSubmissions['remaining_submissions_today_count']) {
      this.globalService.formValidate(this.components, this.formSubmit, this);
    } else {
      this.globalService.showToast('info', 'You have exhausted today\'s submission limit');
    }
  }

  /**
   * Form submit function
   * @param self  context value of this
   */
  formSubmit(self) {
    self.submissionError = '';
    const submissionFile = self.globalService.formItemForLabel(self.components, 'input_file').fileValue;
    if (submissionFile === null || submissionFile === '') {
      self.submissionError = 'Please upload file!';
      return;
    } else if (self.selectedPhase['id'] === undefined) {
      self.submissionError = 'Please select phase!';
      return;
    }

    const FORM_DATA: FormData = new FormData();
    FORM_DATA.append('status', 'submitting');
    FORM_DATA.append('input_file', self.globalService.formItemForLabel(self.components, 'input_file').fileSelected);
    FORM_DATA.append('method_name', self.globalService.formValueForLabel(self.components, 'method_name'));
    FORM_DATA.append('method_description', self.globalService.formValueForLabel(self.components, 'method_description'));
    FORM_DATA.append('project_url', self.globalService.formValueForLabel(self.components, 'project_url'));
    FORM_DATA.append('publication_url', self.globalService.formValueForLabel(self.components, 'publication_url'));
    self.challengeService.challengeSubmission(
      self.challenge['id'],
      self.selectedPhase['id'],
      FORM_DATA,
      () => {
        self.globalService.setFormValueForLabel(self.components, 'input_file', null);
        self.globalService.setFormValueForLabel(self.components, 'method_name', '');
        self.globalService.setFormValueForLabel(self.components, 'method_description', '');
        self.globalService.setFormValueForLabel(self.components, 'project_url', '');
        self.globalService.setFormValueForLabel(self.components, 'publication_url', '');
      }
    );
  }

  /**
   * Edit submission guidelines
   */
  editSubmissionGuideline() {
    const SELF = this;
    SELF.apiCall = (params) => {
      const BODY = JSON.stringify(params);
      SELF.apiService.patchUrl(
        SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id),
        BODY
      ).subscribe(
        data => {
          SELF.submissionGuidelines = data.submission_guidelines;
          SELF.globalService.showToast('success', 'The submission guidelines is successfully updated!', 5);
        },
        err => {
          SELF.globalService.handleApiError(err, true);
          SELF.globalService.showToast('error', err);
        },
        () => {}
      );
    };

    const PARAMS = {
      title: 'Edit Submission Guidelines',
      label: 'submission_guidelines',
      isEditorRequired: true,
      editorContent: this.challenge.submission_guidelines,
      confirm: 'Submit',
      deny: 'Cancel',
      confirmCallback: SELF.apiCall
    };
    SELF.globalService.showModal(PARAMS);
  }

  validateInput(inputValue) {
    this.inputFile = inputValue === null;
  }
}
