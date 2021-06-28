import { Component, OnInit, OnDestroy, QueryList, ViewChildren } from '@angular/core';
import { COMMA, ENTER } from '@angular/cdk/keycodes';
import { MatChipInputEvent } from '@angular/material/chips';
import { Router } from '@angular/router';
import { NGXLogger } from 'ngx-logger';
import * as moment from 'moment';

import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';

import { SelectphaseComponent } from '../../utility/selectphase/selectphase.component';

@Component({
  selector: 'app-challengesettings',
  templateUrl: './challengesettings.component.html',
  styleUrls: ['./challengesettings.component.scss'],
})
export class ChallengesettingsComponent implements OnInit, OnDestroy {

  /**
   * Phase select card components
   */
  @ViewChildren('phaseselect')
  components: QueryList<SelectphaseComponent>;

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Challenge phase list
   */
  phases = [];

  /**
   * Phase selection type (radio button or select box)
   */
  phaseSelectionType = 'selectBox';

  /**
   * Select box list type
   */
  phaseSelectionListType = 'phase';

  /**
   * Currently selected phase
   */
  selectedPhase: any = null;
  
  /**
   * store worker logs
   */
  workerLogs = [];

  /**
   * An interval for fetching the leaderboard data in every 5 seconds
   */
  pollingInterval: any;

  /**
   * Is challenge host
   */
  isChallengeHost = false;

  /**
   * To call the API inside modal for editing the challenge details
   */
  apiCall: any;

  /**
   * Participants banned emails ids
   */
  bannedEmailIds: string[];

  /**
   * Former participants banned emails ids
   */
  formerBannedEmailIds: string[];

  /**
   * Email validation for the banned email ids
   */
  isValidationError = false;

  /**
   * Email error message
   */
  message: string;

  /**
   * publish challenge state and it's icon
   */
  publishChallenge = {
    state: 'Not Published',
    icon: 'fa fa-eye-slash red-text',
  };

  /**
   * Separator key codes
   */
  readonly separatorKeysCodes: number[] = [ENTER, COMMA];

  /**
   * Banned email ids chips property
   */
  visible = true;
  selectable = true;
  removable = true;
  addOnBlur = true;

  /**
   * Input to edit the banned participants emails
   */
  isBannedEmailInputVisible: boolean;

  constructor(
    private challengeService: ChallengeService,
    private globalService: GlobalService,
    private apiService: ApiService,
    private endpointsService: EndpointsService,
    private router: Router,
    private logger: NGXLogger
  ) {}

  ngOnInit() {
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
    });

    this.challengeService.currentPhases.subscribe((phases) => {
      this.phases = phases;
    });  

    this.challengeService.isChallengeHost.subscribe((status) => {
      this.isChallengeHost = status;
    });

    this.challengeService.currentChallengePublishState.subscribe((publishChallenge) => {
      this.publishChallenge.state = publishChallenge.state;
      this.publishChallenge.icon = publishChallenge.icon;
    });

    if (!this.challenge["remote_evaluation"]) {
      this.fetchWorkerLogs();
      this.startLoadingLogs();
    }
  }

  updateView() {
    this.bannedEmailIds = this.challenge.banned_email_ids || [];
    this.formerBannedEmailIds = this.bannedEmailIds.concat(); // Creating deep copy
  }

  /**
   * Add banned email chip
   * @param event current event
   */
  add(event: MatChipInputEvent): void {
    const SELF = this;
    const input = event.input;
    const value = event.value;
    SELF.isValidationError = false;
    SELF.message = '';

    // Add our fruit
    if ((value || '').trim()) {
      if (!SELF.validateEmail(value.trim())) {
        SELF.isValidationError = true;
        SELF.message = 'Please enter a valid email!';
      } else {
        SELF.bannedEmailIds.push(value.trim());
      }
    }

    // Reset the input value
    if (input && !SELF.isValidationError) {
      input.value = '';
    }
  }

  /**
   * Called when a phase is selected (from child component)
   */
  phaseSelected() {
    const SELF = this;
    return (phase) => {
      SELF.selectedPhase = phase;

      SELF.apiCall = (params) => {
        const FORM_DATA: FormData = new FormData();
        for (const key in params) {
          if (params[key]) {
            FORM_DATA.append(key, params[key]);
          }
        }
        SELF.apiService
          .patchFileUrl(
            SELF.endpointsService.updateChallengePhaseDetailsURL(SELF.challenge.id, SELF.selectedPhase['id']),
            FORM_DATA
          )
          .subscribe(
            (data) => {
              SELF.selectedPhase = data;
              SELF.challengeService.fetchPhases(SELF.challenge['id']);
              SELF.globalService.showToast('success', 'The challenge phase details are successfully updated!');
            },
            (err) => {
              SELF.globalService.showToast('error', err);
            },
            () => {this.logger.info('PHASE-UPDATE-FINISHED')}
          );
      };

      const PARAMS = {
        title: 'Edit Challenge Phase Details',
        name: SELF.selectedPhase['name'],
        label: 'description',
        description: SELF.selectedPhase['description'],
        startDate: SELF.selectedPhase['start_date'],
        endDate: SELF.selectedPhase['end_date'],
        maxSubmissionsPerDay: SELF.selectedPhase['max_submissions_per_day'],
        maxSubmissionsPerMonth: SELF.selectedPhase['max_submissions_per_month'],
        maxSubmissions: SELF.selectedPhase['max_submissions'],
        confirm: 'Submit',
        deny: 'Cancel',
        confirmCallback: SELF.apiCall,
      };
      SELF.globalService.showEditPhaseModal(PARAMS);
    };
  } 

  /**
   * Remove banned email chip
   * @param email Banned email id
   */
  remove(email): void {
    const SELF = this;
    const index = SELF.bannedEmailIds.indexOf(email);

    if (index >= 0) {
      SELF.bannedEmailIds.splice(index, 1);
    }

    // updating the banned Email Ids list
    SELF.updateBannedEmailList();
  }

  validateEmail(email) {
    if (email === '') {
      return true;
    }
    const regex = /^\s*[\w\-\+_]+(\.[\w\-\+_]+)*\@[\w\-\+_]+\.[\w\-\+_]+(\.[\w\-\+_]+)*\s*$/;
    return String(email).search(regex) !== -1;
  }

  reflectChange() {
    if (this.bannedEmailIds.toString() === this.formerBannedEmailIds.toString()) {
      this.globalService.showToast('error', 'No change to reflect!');
    } else if (this.isValidationError) {
      this.globalService.showToast('error', 'Please enter a valid email!');
    } else {
      this.updateBannedEmailList();
    }
  }

  updateBannedEmailList() {
    const SELF = this;
    const BODY = JSON.stringify({
      banned_email_ids: SELF.bannedEmailIds,
    });
    SELF.apiService
      .patchUrl(SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id), BODY)
      .subscribe(
        (data) => {
          SELF.challenge.banned_email_ids = data.banned_email_ids;
          SELF.isBannedEmailInputVisible = false;
          SELF.globalService.showToast('success', 'Banned participant emails are successfully updated!', 5);
          this.formerBannedEmailIds = this.bannedEmailIds.concat(); // Creating deep copy
        },
        (err) => {
          SELF.globalService.handleApiError(err, true);
          SELF.globalService.showToast('error', err);
        },
        () => {}
      );
  }

  /**
   * Close participation function
   */
  stopParticipation(event) {
    event.preventDefault();
    const participationState = this.challenge['is_registration_open'] ? 'Close' : 'Open';
    const closeParticipationMsg = 'Participation is closed successfully';
    const openParticipationMsg = 'Participation is opened successfully';

    this.apiCall = () => {
      if (this.isChallengeHost && this.challenge['id'] !== null) {
        const BODY = JSON.stringify({
          is_registration_open: !this.challenge['is_registration_open'],
        });
        this.apiService
          .patchUrl(this.endpointsService.editChallengeDetailsURL(this.challenge.creator.id, this.challenge.id), BODY)
          .subscribe(
            () => {
              this.challenge['is_registration_open'] = !this.challenge['is_registration_open'];
              if (this.challenge['is_registration_open']) {
                this.globalService.showToast('success', openParticipationMsg, 5);
              } else {
                this.globalService.showToast('success', closeParticipationMsg, 5);
              }
            },
            (err) => {
              this.globalService.handleApiError(err, true);
              this.globalService.showToast('error', err);
            },
            () => {}
          );
      }
    };

    const PARAMS = {
      title: participationState + ' participation in the challenge?',
      content: '',
      confirm: "Yes, I'm sure",
      deny: 'No',
      confirmCallback: this.apiCall,
    };
    this.globalService.showConfirm(PARAMS);
  }

  /**
   * Edit challenge title function
   */
  editChallengeTitle() {
    const SELF = this;

    SELF.apiCall = (params) => {
      const BODY = JSON.stringify(params);
      SELF.apiService
        .patchUrl(SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id), BODY)
        .subscribe(
          (data) => {
            SELF.challenge.title = data.title;
            SELF.globalService.showToast('success', 'The challenge title is  successfully updated!', 5);
          },
          (err) => {
            SELF.globalService.handleApiError(err, true);
            SELF.globalService.showToast('error', err);
          },
          () => {}
        );
    };

    const PARAMS = {
      title: 'Edit Challenge Title',
      content: '',
      confirm: 'Submit',
      deny: 'Cancel',
      form: [
        {
          name: 'editChallengeTitle',
          isRequired: true,
          label: 'title',
          placeholder: 'Challenge Title',
          type: 'text',
          value: this.challenge.title,
        },
      ],
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }

  /**
   * Edit terms and conditions of the challenge
   */
  editTermsAndConditions() {
    const SELF = this;
    SELF.apiCall = (params) => {
      const BODY = JSON.stringify(params);
      SELF.apiService
        .patchUrl(SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id), BODY)
        .subscribe(
          (data) => {
            SELF.challenge.terms_and_conditions = data.terms_and_conditions;
            this.updateView();
            SELF.globalService.showToast('success', 'The terms and conditions are successfully updated!', 5);
          },
          (err) => {
            SELF.globalService.handleApiError(err, true);
            SELF.globalService.showToast('error', err);
          },
          () => this.logger.info('EDIT-TERMS-AND-CONDITIONS-FINISHED')
        );
    };

    /**
     * Parameters of the modal
     */
    const PARAMS = {
      title: 'Edit Terms And Conditions',
      label: 'terms_and_conditions',
      isEditorRequired: true,
      editorContent: this.challenge.terms_and_conditions,
      confirm: 'Submit',
      deny: 'Cancel',
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }


  /**
   * Delete challenge
   */
  deleteChallenge() {
    const SELF = this;
    const redirectTo = '/dashboard';

    SELF.apiCall = () => {
      const BODY = JSON.stringify({});
      SELF.apiService.postUrl(SELF.endpointsService.deleteChallengeURL(SELF.challenge.id), BODY).subscribe(
        (data) => {
          SELF.router.navigate([redirectTo]);
          SELF.globalService.showToast('success', 'The Challenge is successfully deleted!', 5);
        },
        (err) => {
          SELF.globalService.handleApiError(err, true);
          SELF.globalService.showToast('error', err);
        },
        () => {}
      );
    };

    const PARAMS = {
      title: 'Delete Challenge',
      content: '',
      confirm: 'I understand consequences, delete the challenge',
      deny: 'Cancel',
      form: [
        {
          name: 'challegenDeleteInput',
          isRequired: true,
          label: '',
          placeholder: 'Please type in the name of the challenge to confirm',
          type: 'text',
          value: '',
        },
      ],
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }

  /**
   * Edit challenge start and end date function
   */
  challengeDateDialog() {
    const SELF = this;
    SELF.apiCall = (params) => {
      if (new Date(params.start_date).valueOf() < new Date(params.end_date).valueOf()) {
        const BODY = JSON.stringify({
          start_date: new Date(params.start_date).toISOString(),
          end_date: new Date(params.end_date).toISOString(),
        });
        SELF.apiService
          .patchUrl(SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id), BODY)
          .subscribe(
            (data) => {
              SELF.challenge.start_date = data.start_date;
              SELF.challenge.end_date = data.end_date;
              SELF.globalService.showToast('success', 'The Challenge start and end date successfully updated!', 5);
            },
            (err) => {
              SELF.globalService.handleApiError(err, true);
              SELF.globalService.showToast('error', err);
            },
            () => {}
          );
      } else {
        SELF.globalService.showToast('error', 'The challenge start date cannot be same or greater than end date.', 5);
      }
    };
    const PARAMS = {
      title: 'Edit Challenge Start and End Date',
      content: '',
      confirm: 'Confirm',
      deny: 'Cancel',
      form: [
        {
          isRequired: false,
          label: 'start_date',
          placeholder: 'Start Date and Time',
          type: 'text',
          value: moment(this.challenge.start_date).format('MM-DD-YYYY hh:mm a'),
        },
        {
          isRequired: false,
          label: 'end_date',
          placeholder: 'End Date and Time',
          type: 'text',
          value: moment(this.challenge.end_date).format('MM-DD-YYYY hh:mm a'),
        },
      ],
      isButtonDisabled: true,
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }

  /**
   * Edit evaluation criteria of the challenge
   */
  editEvaluationCriteria() {
    const SELF = this;
    SELF.apiCall = (params) => {
      const BODY = JSON.stringify(params);
      SELF.apiService
        .patchUrl(SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id), BODY)
        .subscribe(
          (data) => {
            SELF.challenge.evaluation_details = data.evaluation_details;
            this.updateView();
            SELF.globalService.showToast('success', 'The evaluation details is successfully updated!', 5);
          },
          (err) => {
            SELF.globalService.handleApiError(err, true);
            SELF.globalService.showToast('error', err);
          },
          () => this.logger.info('EDIT-CHALLENGE-EVALUATION-DETAILS-FINISHED')
        );
    };

    /**
     * Parameters of the modal
     */
    const PARAMS = {
      title: 'Edit Evaluation Details',
      label: 'evaluation_details',
      isEditorRequired: true,
      editorContent: this.challenge.evaluation_details,
      confirm: 'Submit',
      deny: 'Cancel',
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }

  /**
   * Edit evaluation script of the challenge
   */
  editEvaluationScript() {
    const SELF = this;
    SELF.apiCall = (params) => {
      const FORM_DATA: FormData = new FormData();
      FORM_DATA.append('evaluation_script', params['evaluation_script']);
      SELF.apiService
        .patchFileUrl(
          SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id),
          FORM_DATA
        )
        .subscribe(
          (data) => {
            SELF.globalService.showToast('success', 'The evaluation script is successfully updated!');
          },
          (err) => {
            SELF.globalService.showToast('error', err);
          },
          () => this.logger.info('EDIT-EVALUATION-SCRIPT-FINISHED')
        );
    };

    /**
     * Parameters of the modal
     */
    const PARAMS = {
      title: 'Edit Evaluation Script',
      confirm: 'Submit',
      deny: 'Cancel',
      form: [
        {
          name: 'evaluationScript',
          isRequired: true,
          label: 'evaluation_script',
          placeholder: '',
          type: 'file',
          value: '',
        },
      ],
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }

  /**
   * Edit challenge image function
   */
  editChallengeImage() {
    const SELF = this;
    SELF.apiCall = (params) => {
      const FORM_DATA: FormData = new FormData();
      FORM_DATA.append('image', params['image']);
      SELF.apiService
        .patchFileUrl(
          SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id),
          FORM_DATA
        )
        .subscribe(
          (data) => {
            SELF.challenge.image = data.image;
            SELF.globalService.showToast('success', 'The Challenge image successfully updated!', 5);
          },
          (err) => {
            SELF.globalService.handleApiError(err, true);
            SELF.globalService.showToast('error', err);
          },
          () => {}
        );
    };

    /**
     * Parameters of the modal
     */
    const PARAMS = {
      title: 'Edit Challenge Image',
      content: '',
      confirm: 'Submit',
      deny: 'Cancel',
      form: [
        {
          name: 'Challenge Image',
          isRequired: true,
          label: 'image',
          placeholder: '',
          type: 'file',
          value: '',
        },
      ],
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }

  /**
   * Edit challenge overview function
   */

  editChallengeOverview() {
    const SELF = this;

    SELF.apiCall = (params) => {
      const BODY = JSON.stringify(params);
      SELF.apiService
        .patchUrl(SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id), BODY)
        .subscribe(
          (data) => {
            SELF.challenge.description = data.description;
            SELF.globalService.showToast('success', 'The description is successfully updated!', 5);
          },
          (err) => {
            SELF.globalService.handleApiError(err, true);
            SELF.globalService.showToast('error', err);
          },
          () => this.logger.info('EDIT-CHALLENGE-DESCRIPTION-FINISHED')
        );
    };

    const PARAMS = {
      title: 'Edit Challenge Description',
      label: 'description',
      isEditorRequired: true,
      editorContent: this.challenge.description,
      confirm: 'Submit',
      deny: 'Cancel',
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }

  /**
   * API call to manage the worker from UI.
   * Response data will be like: {action: "Success" or "Failure", error: <String to include only if action is Failure.>}
   */
  manageWorker(action) {
    const SELF = this;
    const API_PATH = SELF.endpointsService.manageWorkerURL(SELF.challenge['id'], action);
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
    if(this.challenge['id']) {
      const API_PATH = this.endpointsService.getLogsURL(this.challenge['id']);
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

  /**
   * Publish challenge click function
   */
  togglePublishChallengeState() {
    const SELF = this;
    let toggleChallengePublishState, isPublished;
    if (this.publishChallenge.state === 'Published') {
      toggleChallengePublishState = 'private';
      isPublished = false;
    } else {
      toggleChallengePublishState = 'public';
      isPublished = true;
    }
    SELF.apiCall = () => {
      const BODY = JSON.stringify({
        published: isPublished,
      });
      SELF.apiService
        .patchUrl(SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id), BODY)
        .subscribe(
          (data) => {
            if (isPublished) {
              this.publishChallenge.state = 'Published';
              this.publishChallenge.icon = 'fa fa-eye green-text';
            } else {
              this.publishChallenge.state = 'Not Published';
              this.publishChallenge.icon = 'fa fa-eye-slash red-text';
            }
            SELF.globalService.showToast(
              'success',
              'The challenge was successfully made ' + toggleChallengePublishState,
              5
            );
          },
          (err) => {
            SELF.globalService.handleApiError(err, true);
            SELF.globalService.showToast('error', err);
          },
          () => this.logger.info('PUBLISH-CHALLENGE-UPDATE-FINISHED')
        );
    };

    const PARAMS = {
      title: 'Make this challenge ' + toggleChallengePublishState + '?',
      content: '',
      confirm: "Yes, I'm sure",
      deny: 'No',
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showConfirm(PARAMS);
  }

}
