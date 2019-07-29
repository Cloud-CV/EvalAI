import { Component, OnInit } from '@angular/core';
import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import {COMMA, ENTER} from '@angular/cdk/keycodes';
import {MatChipInputEvent} from '@angular/material/chips';

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
   * Participants banned emails ids
   */
  bannedEmailIds: string[];

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

  constructor(private challengeService: ChallengeService, private globalService: GlobalService,
              private apiService: ApiService, private endpointsService: EndpointsService) { }

  ngOnInit() {
    this.challengeService.currentChallenge.subscribe(
      challenge => {
        this.challenge = challenge;
        this.updateView();
    });
  }

  updateView() {
    this.bannedEmailIds = this.challenge.banned_email_ids;
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

    if (value !== '' && !SELF.isValidationError) {
      SELF.updateBannedEmailList();
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
    const index = this.bannedEmailIds.indexOf(email);

    if (index >= 0) {
      this.bannedEmailIds.splice(index, 1);
    }
    SELF.updateBannedEmailList();
  }

  validateEmail(email) {
    if (email === '') {
      return true;
    }
    const regex = /^\s*[\w\-\+_]+(\.[\w\-\+_]+)*\@[\w\-\+_]+\.[\w\-\+_]+(\.[\w\-\+_]+)*\s*$/;
    return String(email).search (regex) !== -1;
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
        },
        err => {
          SELF.globalService.handleApiError(err, true);
          SELF.globalService.showToast('error', err);
        },
        () => {}
      );
  }

}
