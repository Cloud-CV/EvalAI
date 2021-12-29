import { Component, OnInit, QueryList, ViewChildren } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { NGXLogger } from 'ngx-logger';

// import service
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengesubmit',
  templateUrl: './challengesubmit.component.html',
  styleUrls: ['./challengesubmit.component.scss'],
})
export class ChallengesubmitComponent implements OnInit {
  /**
   * Input error Message
   */
  inputErrorMessage = '';

  /**
   * Is input valid
   */
  validFileUrl = false;

  /**
   * Is file url input
   */
  isSubmissionUsingUrl: any;

  /**
   * Is submission through CLI
   */
  isSubmissionUsingCli: any;

  /**
   * If phase has been selected
   */
  isPhaseSelected = false;

  /**
   * Is user logged in
   */
  isLoggedIn = false;

  /**
   * Is submission submitted
   */
  isSubmitted = false;

  /**
   * Is submission submitted
   */
  isPublicSubmission = true;

  /**
   * Is submission allowed by host
   */
  isLeaderboardPublic = false;

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
   * Submission error
   */
  submissionError = '';

  /**
   * Guidelines text
   */
  submissionGuidelines = '';

  /**
   * Stores the attributes format and phase ID for all the phases of a challenge.
   */
  submissionMetaAttributes = [];

  /**
   * Stores the attributes while making a submission for a selected phase.
   */
  metaAttributesforCurrentSubmission = null;

  /**
   * Stores the default meta attributes for all the phases of a challenge.
   */
   defaultMetaAttributes = [];

  /**
   * Stores the default meta attributes for a selected phase.
   */
  defaultMetaAttributesforCurrentPhase = null;
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
   * Cli version
   */
  cliVersion = '';

  /**
   * Auth token
   */
  authToken = '';

  /**
   * Phase selection type (radio button or select box)
   */
  phaseSelectionType = 'radioButton';

  /**
   * Select box list type
   */
  phaseSelectionListType = 'phase';

  /**
   * Api call inside the modal to edit the submission guidelines
   */
  apiCall: any;

  /**
   * Selected phase submission conditions
   * @param showSubmissionDetails show the selected phase submission details
   * @param showClock when max submissions per day exceeded
   * @param maxExceeded max submissions exceeded
   * @param remainingSubmissions remaining submissions details
   * @param maxExceededMessage message for max submissions exceeded
   * @param clockMessage message for max submissions per day exceeded
   */
  selectedPhaseSubmissions = {
    showSubmissionDetails: false,
    showClock: false,
    maxExceeded: false,
    remainingSubmissions: {},
    maxExceededMessage: '',
    clockMessage: '',
  };

  /**
   * Phase remaining submissions for docker based challenge
   */
  phaseRemainingSubmissions: any;

  /**
   * Flog for phase if submissions max exceeded, details, clock
   */
  phaseRemainingSubmissionsFlags = {};

  /**
   * Phase remaining submissions countdown (days, hours, minutes, seconds)
   */
  phaseRemainingSubmissionsCountdown = {};

  /**
   * Clock variables
   * @param days number of days remaining
   * @param hours number of hours remaining
   * @param minutes number of minutes remaining
   * @param seconds number of seconds remaining
   * @param remainingTime remaining time (in seconds) for submission of a challenge phase
   */
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  remainingTime: number;

  /**
   * Is clock initialised
   */
  isClockStarted: boolean;

  /**
   * Set interval timer
   */
  timer: any;

  /**
   * Component Class
   */
  @ViewChildren('formsubmit')
  components: QueryList<ChallengesubmitComponent>;

  /**
   * Constructor.
   * @param authService  AuthService Injection.
   * @param router  Router Injection.
   * @param route  ActivatedRoute Injection.
   * @param challengeService  ChallengeService Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  Router Injection.
   * @param endpointsService  EndpointsService Injection.
   */
  constructor(
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private challengeService: ChallengeService,
    private globalService: GlobalService,
    private apiService: ApiService,
    private endpointsService: EndpointsService,
    private logger: NGXLogger
  ) {}

  /**
   * Component on intialization.
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.routerPublic = this.router;
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
      this.isActive = this.challenge['is_active'];
      this.submissionGuidelines = this.challenge['submission_guidelines'];
      if (this.challenge.cli_version !== null) {
        this.cliVersion = this.challenge.cli_version;
      }
    });
    this.challengeService.currentParticipationStatus.subscribe((status) => {
      this.isParticipated = status;
      if (!status) {
        this.router.navigate(['../participate'], { relativeTo: this.route });
      }
    });
    this.challengeService.currentPhases.subscribe((phases) => {
      this.phases = phases;
      this.filteredPhases = this.phases.filter((phase) => phase['is_active'] === true);
      for (let j = 0; j < this.phases.length; j++) {
        if (phases[j].is_public === false) {
          this.phases[j].showPrivate = true;
        } else {
          this.phases[j].showPrivate = false;
        }
      }
    });

    this.challengeService.isChallengeHost.subscribe((status) => {
      this.isChallengeHost = status;
    });

    this.challengeService.isChallengeHost.subscribe((status) => {
      this.isChallengeHost = status;
    });

    if (this.challenge.is_docker_based) {
      this.displayDockerSubmissionInstructions(this.challenge.id, this.isParticipated);
    }
    this.authToken = this.globalService.getData('refreshJWT');
  }

  /**
   * @param SELF current context
   * @param eachPhase particular phase of a challenge
   */
  countDownTimer(SELF, eachPhase) {
    if (!SELF.isClockStarted) {
      SELF.remainingTime = parseInt(eachPhase.limits.remaining_time, 10);
    }
    SELF.days = Math.floor(SELF.remainingTime / 24 / 60 / 60);
    const hoursLeft = Math.floor(SELF.remainingTime - SELF.days * 86400);
    SELF.hours = Math.floor(hoursLeft / 3600);
    const minutesLeft = Math.floor(hoursLeft - SELF.hours * 3600);
    SELF.minutes = Math.floor(minutesLeft / 60);
    SELF.seconds = Math.floor(SELF.remainingTime % 60);

    if (SELF.days < 10) {
      SELF.days = '0' + SELF.days;
    }
    if (SELF.hours < 10) {
      SELF.hours = '0' + SELF.hours;
    }
    if (SELF.minutes < 10) {
      SELF.minutes = '0' + SELF.minutes;
    }
    if (SELF.seconds < 10) {
      SELF.seconds = '0' + SELF.seconds;
    }

    // Used when the challenge is docker based
    SELF.phaseRemainingSubmissionsCountdown[eachPhase.id] = {
      days: SELF.days,
      hours: SELF.hours,
      minutes: SELF.minutes,
      seconds: SELF.seconds,
    };
    if (SELF.remainingTime === 0) {
      SELF.selectedPhaseSubmissions.showSubmissionDetails = true;
      SELF.phaseRemainingSubmissionsFlags[eachPhase.id] = 'showSubmissionDetails';
    } else {
      SELF.remainingTime--;
    }
    SELF.isClockStarted = true;
  }

  /**
   * @param challenge challenge id
   * @param isParticipated Is user a participant
   */
  displayDockerSubmissionInstructions(challenge, isParticipated) {
    if (isParticipated) {
      const API_PATH = this.endpointsService.challengeSubmissionsRemainingURL(challenge);
      const SELF = this;
      this.apiService.getUrl(API_PATH).subscribe(
        (data) => {
          SELF.phaseRemainingSubmissions = data;
          const details = SELF.phaseRemainingSubmissions.phases;
          for (let i = 0; i < details.length; i++) {
            if (details[i].limits.submission_limit_exceeded === true) {
              SELF.phaseRemainingSubmissionsFlags[details[i].id] = 'maxExceeded';
            } else if (details[i].limits.remaining_submissions_today_count > 0) {
              SELF.phaseRemainingSubmissionsFlags[details[i].id] = 'showSubmissionDetails';
            } else {
              const eachPhase = details[i];
              SELF.phaseRemainingSubmissionsFlags[details[i].id] = 'showClock';
              setInterval(function () {
                SELF.countDownTimer(SELF, eachPhase);
              }, 1000);
              SELF.countDownTimer(SELF, eachPhase);
            }
          }
        },
        (err) => {
          SELF.globalService.handleApiError(err);
        },
        () => this.logger.info('Remaining submissions fetched for docker based challenge')
      );
    }
  }

  /**
   * Fetch remaining submissions for a challenge phase.
   * @param challenge  challenge id
   * @param phase  phase id
   */
  fetchRemainingSubmissions(challenge, phase) {
    const API_PATH = this.endpointsService.challengeSubmissionsRemainingURL(challenge);
    const SELF = this;
    clearInterval(SELF.timer);
    SELF.isClockStarted = false;
    SELF.selectedPhaseSubmissions.showClock = false;
    SELF.selectedPhaseSubmissions.showSubmissionDetails = false;
    SELF.selectedPhaseSubmissions.maxExceeded = false;
    this.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        let phaseDetails, eachPhase;
        for (let i = 0; i < data.phases.length; i++) {
          if (data.phases[i].id === phase) {
            eachPhase = data.phases[i];
            phaseDetails = data.phases[i].limits;
            break;
          }
        }
        if (phaseDetails.submission_limit_exceeded) {
          this.selectedPhaseSubmissions.maxExceeded = true;
          this.selectedPhaseSubmissions.maxExceededMessage = phaseDetails.message;
        } else if (phaseDetails.remaining_submissions_today_count > 0) {
          this.selectedPhaseSubmissions.remainingSubmissions = phaseDetails;
          this.selectedPhaseSubmissions.showSubmissionDetails = true;
        } else {
          this.selectedPhaseSubmissions.showClock = true;
          this.selectedPhaseSubmissions.clockMessage = phaseDetails;
          SELF.timer = setInterval(function () {
            SELF.countDownTimer(SELF, eachPhase);
          }, 1000);
          SELF.countDownTimer(SELF, eachPhase);
        }
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        this.logger.info('Remaining submissions fetched for challenge-phase', challenge, phase);
      }
    );
  }

  /**
   * Store Meta Attributes for a particular challenge phase.
   */
  storeMetadata(data) {
    for (let i = 0; i < data.count; i++) {
      if (data.results[i].submission_meta_attributes) {
        const attributes = data.results[i].submission_meta_attributes;
        attributes.forEach(function (attribute) {
          if (attribute['type'] === 'checkbox') {
            attribute['values'] = [];
          } else {
            attribute['value'] = null;
          }
        });
        const detail = { phaseId: data.results[i].id, attributes: attributes };
        this.submissionMetaAttributes.push(detail);
      } else {
        const detail = { phaseId: data.results[i].id, attributes: null };
        this.submissionMetaAttributes.push(detail);
      }
      if (data.results[i].default_submission_meta_attributes) {
        const attributes = data.results[i].default_submission_meta_attributes;
        var attributeDict = {};
        attributes.forEach(function (attribute) {
          attributeDict[attribute["name"]] = attribute;
        });
        const detail = { phaseId: data.results[i].id, attributes: attributeDict };
        this.defaultMetaAttributes.push(detail);
      } else {
        const detail = { phaseId: data.results[i].id, attributes: {} };
        this.defaultMetaAttributes.push(detail);
      }
    }
  }

  /**
   * Fetch Meta Attributes for a particular challenge phase.
   * @param challenge  challenge id
   * @param phase  phase id
   */
  getMetaDataDetails(challenge, phaseId) {
    const API_PATH = this.endpointsService.challengePhaseURL(challenge);
    const SELF = this;
    this.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        SELF.storeMetadata(data);
        // Loads attributes of a phase into this.submissionMetaAttributes
        this.metaAttributesforCurrentSubmission = this.submissionMetaAttributes.find(function (element) {
          return element['phaseId'] === phaseId;
        }).attributes;
        this.defaultMetaAttributesforCurrentPhase = this.defaultMetaAttributes.find(function (element) {
          return element['phaseId'] === phaseId;
        }).attributes;
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );
  }

  /**
   * Clear the data of metaAttributesforCurrentSubmission
   */
  clearMetaAttributeValues() {
    if (this.metaAttributesforCurrentSubmission != null) {
      this.metaAttributesforCurrentSubmission.forEach(function (attribute) {
        if (attribute.type === 'checkbox') {
          attribute.values = [];
        } else {
          attribute.value = null;
        }
      });
    }
  }

  /**
   * Called when a phase is selected (from child components)
   */
  phaseSelected() {
    const SELF = this;
    return (phase) => {
      SELF.selectedPhase = phase;
      SELF.isPhaseSelected = true;
      SELF.isLeaderboardPublic = phase['leaderboard_public'];
      if (SELF.challenge['id'] && phase['id']) {
        SELF.getMetaDataDetails(SELF.challenge['id'], phase['id']);
        SELF.fetchRemainingSubmissions(SELF.challenge['id'], phase['id']);
        SELF.clearMetaAttributeValues();
        SELF.submissionError = '';
        if (SELF.components) {
          SELF.components['_results'].forEach((element) => {
            element.value = '';
            element.message = '';
          });
        }
      }
    };
  }

  /**
   * Form validate function
   */
  formValidate() {
    if (this.selectedPhaseSubmissions.remainingSubmissions['remaining_submissions_today_count']) {
      this.globalService.formValidate(this.components, this.formSubmit, this);
      if (this.isSubmitted) {
        this.router.navigate(['../my-submissions'], { relativeTo: this.route });
      }
    } else {
      this.globalService.showToast('info', "You have exhausted today's submission limit");
    }
  }

  /**
   * Form submit function
   * @param self  context value of this
   */
  formSubmit(self) {
    self.submissionError = '';
    let metaValue = true;
    const submissionFile = self.globalService.formItemForLabel(self.components, 'input_file').fileValue;
    const submissionProjectUrl = self.globalService.formValueForLabel(self.components, 'project_url');
    const submissionPublicationUrl = self.globalService.formValueForLabel(self.components, 'publication_url');
    const submissionFileUrl = self.globalService.formItemForLabel(self.components, 'file_url');
    const regex = new RegExp(/(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-/]))?/);
    if (!self.isSubmissionUsingUrl && (submissionFile === null || submissionFile === '')) {
      self.submissionError = 'Please upload file!';
      return;
    } else if (self.isSubmissionUsingUrl && submissionFileUrl !== '' && !self.validFileUrl) {
      self.submissionError = 'Please enter a valid Submission URL!';
      return;
    } else if (self.selectedPhase['id'] === undefined) {
      self.submissionError = 'Please select phase!';
      return;
    } else if (submissionProjectUrl !== '' && !regex.test(submissionProjectUrl)) {
      self.submissionError = 'Please provide a valid project URL!';
      return;
    } else if (submissionPublicationUrl !== '' && !regex.test(submissionPublicationUrl)) {
      self.submissionError = 'Please provide a valid publication URL!';
      return;
    }
    if (self.metaAttributesforCurrentSubmission != null) {
      self.metaAttributesforCurrentSubmission.forEach((attribute) => {
        if (attribute.required === true) {
          if (attribute.type === 'checkbox') {
            if (attribute.values.length === 0) {
              metaValue = false;
            }
          } else {
            if (attribute.value === null || attribute.value === undefined) {
              metaValue = false;
            }
          }
        }
      });
    }
    if (metaValue !== true) {
      self.submissionError = 'Please provide input for meta attributes!';
      return;
    }

    const FORM_DATA: FormData = new FormData();
    FORM_DATA.append('status', 'submitting');
    if (!self.isSubmissionUsingUrl) {
      FORM_DATA.append('input_file', self.globalService.formItemForLabel(self.components, 'input_file').fileSelected);
    } else if (self.validFileUrl && self.isSubmissionUsingUrl) {
      FORM_DATA.append('file_url', self.globalService.formValueForLabel(self.components, 'file_url'));
    }
    FORM_DATA.append('is_public', self.isPublicSubmission);
    FORM_DATA.append('method_name', self.globalService.formValueForLabel(self.components, 'method_name'));
    FORM_DATA.append('method_description', self.globalService.formValueForLabel(self.components, 'method_description'));
    FORM_DATA.append('project_url', self.globalService.formValueForLabel(self.components, 'project_url'));
    FORM_DATA.append('publication_url', self.globalService.formValueForLabel(self.components, 'publication_url'));
    FORM_DATA.append('submission_metadata', JSON.stringify(self.metaAttributesforCurrentSubmission));
    self.challengeService.challengeSubmission(self.challenge['id'], self.selectedPhase['id'], FORM_DATA, () => {
      if (!self.isSubmissionUsingUrl) {
        self.globalService.setFormValueForLabel(self.components, 'input_file', null);
      } else if (self.validFileUrl && self.isSubmissionUsingUrl) {
        self.globalService.setFormValueForLabel(self.components, 'file_url', '');
      }
      self.globalService.setFormValueForLabel(self.components, 'method_name', '');
      self.globalService.setFormValueForLabel(self.components, 'method_description', '');
      self.globalService.setFormValueForLabel(self.components, 'project_url', '');
      self.globalService.setFormValueForLabel(self.components, 'publication_url', '');
    });
    self.isSubmitted = true;
  }

  copyTextToClipboard(ref: HTMLElement) {
    const textBox = document.createElement('textarea');
    textBox.style.position = 'fixed';
    textBox.style.left = '0';
    textBox.style.top = '0';
    textBox.style.opacity = '0';
    textBox.value = ref.innerText.split('$ ')[1];
    document.body.appendChild(textBox);
    textBox.focus();
    textBox.select();
    document.execCommand('copy');
    document.body.removeChild(textBox);

    this.globalService.showToast('success', 'Command copied to clipboard');
  }

  /**
   * Edit submission guidelines
   */
  editSubmissionGuideline() {
    const SELF = this;
    SELF.apiCall = (params) => {
      const BODY = JSON.stringify(params);
      SELF.apiService
        .patchUrl(SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id), BODY)
        .subscribe(
          (data) => {
            SELF.submissionGuidelines = data.submission_guidelines;
            SELF.globalService.showToast('success', 'The submission guidelines is successfully updated!', 5);
          },
          (err) => {
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
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }

  /**
   * Edit challenge overview with file function
   */
   editSubmissionGuidelineUpload() {
    const SELF = this;
    SELF.apiCall = (params) => {
      const FORM_DATA: FormData = new FormData();
      FORM_DATA.append('submission_guidelines_file', params['submission_guidelines_file']);
      SELF.apiService
        .patchFileUrl(
          SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id),
          FORM_DATA
        )
        .subscribe(
          (data) => {
            SELF.challenge.submission_guidelines = data.submission_guidelines;   
            SELF.globalService.showToast('success', 'The submission guidelines are successfully updated!', 5);
          },
          (err) => {
            SELF.globalService.handleApiError(err, true);
            SELF.globalService.showToast('error', err);
          },
          () => this.logger.info('EDIT-CHALLENGE-DESCRIPTION-FINISHED')
        );
    };

    /**
     * Parameters of the modal
     */
    const PARAMS = {
      title: 'Edit Submission Guidelines',
      content: '',
      confirm: 'Submit',
      deny: 'Cancel',
      form: [
        {
          name: 'Submission Guidelines',
          isRequired: true,
          label: 'submission_guidelines_file',
          placeholder: '',
          type: 'file',
          value: '',
        },
      ],
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }

  validateInput(inputValue) {
    const regex = new RegExp(/(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-/]))?/);
    const validExtensions = ['json', 'zip', 'txt', 'tsv', 'gz', 'csv', 'h5', 'npy'];
    if (this.isSubmissionUsingUrl) {
      if (regex.test(inputValue)) {
        this.inputErrorMessage = '';
        this.validFileUrl = true;
      } else {
        this.inputErrorMessage = 'Please enter a valid URL!';
        this.validFileUrl = false;
      }
    } else {
      const extension = inputValue.split('.').pop();
      if (!validExtensions.includes(extension)) {
        this.inputErrorMessage = 'Please enter a valid File!';
        this.validFileUrl = false;
      } else if (validExtensions.includes(extension)) {
        this.inputErrorMessage = '';
        this.validFileUrl = true;
      }
    }
  }

  // unchecking checked options
  toggleSelection(attribute, value) {
    const idx = attribute.values.indexOf(value);
    if (idx > -1) {
      attribute.values.splice(idx, 1);
    } else {
      attribute.values.push(value);
    }
  }
}
