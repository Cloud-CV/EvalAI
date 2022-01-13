import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';

@Component({
  selector: 'app-challengediscuss',
  templateUrl: './challengediscuss.component.html',
  styleUrls: ['./challengediscuss.component.scss'],
})
export class ChallengediscussComponent implements OnInit {
  /**
   * Is user logged in
   */
  isLoggedIn = false;

  /**
   * Is challenge host
   */
  isChallengeHost = false;

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
   * To call the API inside modal for editing the challenge forum URL
   */
  apiCall: any;

  constructor(
    private authService: AuthService,
    private router: Router,
    private challengeService: ChallengeService,
    private globalService: GlobalService,
    private apiService: ApiService,
    private endpointsService: EndpointsService
  ) {}

  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.routerPublic = this.router;
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
    });
    this.challengeService.isChallengeHost.subscribe((status) => {
      this.isChallengeHost = status;
    });
  }

  editForumURL() {
    const SELF = this;
    SELF.apiCall = (params) => {
      const BODY = JSON.stringify(params);
      SELF.apiService
        .patchUrl(SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id), BODY)
        .subscribe(
          (data) => {
            SELF.challenge.forum_url = data.forum_url;
            SELF.globalService.showToast('success', 'The challenge forum url is successfully updated!', 5);
          },
          (err) => {
            SELF.globalService.showToast('error', 'Please enter a valid URL', 5);
          },
          () => {}
        );
    };

    /**
     * Parameters of the modal
     */
    const PARAMS = {
      title: 'Change Forum URL',
      content: '',
      confirm: 'Confirm',
      deny: 'Cancel',
      form: [
        {
          isRequired: true,
          label: 'forum_url',
          placeholder: 'Forum URL',
          value: this.challenge.forum_url,
          type: 'text',
        },
      ],
      isButtonDisabled: true,
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }
}
