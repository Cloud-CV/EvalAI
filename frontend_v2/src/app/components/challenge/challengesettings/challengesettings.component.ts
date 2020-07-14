import { Component, OnInit } from '@angular/core';
import {COMMA, ENTER} from '@angular/cdk/keycodes';
import {MatChipInputEvent} from '@angular/material/chips';
import { Router } from '@angular/router';
import * as moment from 'moment';

import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';

@Component({
  selector: 'app-challengesettings',
  templateUrl: './challengesettings.component.html',
  styleUrls: ['./challengesettings.component.scss']
})
export class ChallengesettingsComponent implements OnInit {

  /**
   * Challenge object
   */
  challenge: any;

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

  constructor(private challengeService: ChallengeService,
              private globalService: GlobalService,
              private apiService: ApiService,
              private endpointsService: EndpointsService,
              private router: Router) { }

  ngOnInit() {
    this.challengeService.currentChallenge.subscribe(
      challenge => {
        this.challenge = challenge;
        this.updateView();
    });
    this.challengeService.isChallengeHost.subscribe(status => {
      this.isChallengeHost = status;
    });
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
    return String(email).search (regex) !== -1;
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
      banned_email_ids: SELF.bannedEmailIds
    });
    SELF.apiService.patchUrl(
      SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id),
      BODY
    ).subscribe(
        data => {
          SELF.challenge.banned_email_ids = data.banned_email_ids;
          SELF.isBannedEmailInputVisible = false;
          SELF.globalService.showToast('success', 'Banned participant emails are successfully updated!', 5);
          this.formerBannedEmailIds = this.bannedEmailIds.concat(); // Creating deep copy
        },
        err => {
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
    const participationState = (this.challenge['is_registration_open']) ? 'Close' : 'Open';

    this.apiCall = () => {
      if (this.isChallengeHost && this.challenge['id'] !== null) {
        const BODY = JSON.stringify({
          'is_registration_open': !this.challenge['is_registration_open']
        });
        this.apiService.patchUrl(
          this.endpointsService.editChallengeDetailsURL(this.challenge.creator.id, this.challenge.id),
          BODY
        ).subscribe(
          () => {
            this.challenge['is_registration_open'] = !this.challenge['is_registration_open'];
            this.globalService.showToast(
              'success', 'Participation is ' + participationState.replace('n', 'ne') + 'd successfully', 5
            );
          },
          err => {
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
      confirm: 'Yes, I\'m sure',
      deny: 'No',
      confirmCallback: this.apiCall
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
      SELF.apiService.patchUrl(
        SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id),
        BODY
        ).subscribe(
        data => {
          SELF.challenge.title = data.title;
          SELF.globalService.showToast('success', 'The challenge title is  successfully updated!', 5);
        },
        err => {
          SELF.globalService.handleApiError(err, true);
          SELF.globalService.showToast('error', err);
        },
        () =>  console.log('EDIT-CHALLENGE-TITLE-FINISHED')
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
          value: this.challenge.title
        },
      ],
      confirmCallback: SELF.apiCall
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
      SELF.apiService.postUrl(
        SELF.endpointsService.deleteChallengeURL(SELF.challenge.id),
        BODY
        ).subscribe(
        data => {
          SELF.router.navigate([redirectTo]);
          SELF.globalService.showToast('success', 'The Challenge is successfully deleted!', 5);
        },
        err => {
          SELF.globalService.handleApiError(err, true);
          SELF.globalService.showToast('error', err);
        },
        () => console.log('DELETE-CHALLENGE-FINISHED')
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
          value: ''
        },
      ],
      confirmCallback: SELF.apiCall
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
          'start_date': new Date(params.start_date).toISOString(),
          'end_date': new Date(params.end_date).toISOString()
        });
        SELF.apiService.patchUrl(
          SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id),
          BODY
        ).subscribe(
          data => {
            SELF.challenge.start_date = (data.start_date);
            SELF.challenge.end_date = (data.end_date);
            SELF.globalService.showToast('success', 'The Challenge start and end date successfully updated!', 5);
          },
          err => {
            SELF.globalService.handleApiError(err, true);
            SELF.globalService.showToast('error', err);
          },
          () => console.log('EDIT-CHALLENGE-START-AND-END-DATE-FINISHED')
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
          value: moment(this.challenge.start_date).format('MM-DD-YYYY hh:mm a')
        },
        {
          isRequired: false,
          label: 'end_date',
          placeholder: 'End Date and Time',
          type: 'text',
          value: moment(this.challenge.end_date).format('MM-DD-YYYY hh:mm a')
        }
      ],
      isButtonDisabled: true,
      confirmCallback: SELF.apiCall
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
        SELF.apiService.patchFileUrl(
          SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id),
          FORM_DATA
        ).subscribe(
          data => {
            SELF.globalService.showToast('success', 'The Challenge image successfully updated!', 5);
          },
          err => {
            SELF.globalService.handleApiError(err, true);
            SELF.globalService.showToast('error', err);
          },
          () => console.log('EDIT-CHALLENGE-IMAGE-FINISHED')
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
          value: ''
        }
      ],
      confirmCallback: SELF.apiCall
    };
    SELF.globalService.showModal(PARAMS);
  }
}
