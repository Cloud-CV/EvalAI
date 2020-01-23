import { Component, Inject, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { ChallengeService } from '../../services/challenge.service';
import { EndpointsService } from '../../services/endpoints.service';
import { Meta } from '@angular/platform-browser';
import { DOCUMENT } from '@angular/common';

/**
 * Component Class
 */
@Component({
  selector: 'app-challenge',
  templateUrl: './challenge.component.html',
  styleUrls: ['./challenge.component.scss']
})
export class ChallengeComponent implements OnInit {

  /**
   * Router local instance
   */
  localRouter: any;

  /**
   * Challenge id
   */
  id: any;

  /**
   * Is challenge starred
   */
  isStarred = false;

  /**
   * Is challenge host
   */
  isChallengeHost = false;

  /**
   * publish challenge state and it's icon
   */
  publishChallenge = {
    'state': 'Not Published',
    'icon': 'fa fa-eye-slash red-text'
  };

  /**
   * Is participated in Challenge
   */
  isParticipated = false;

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Challenge stars
   */
  stars: any;

  /**
   * Is logged in the Challenge
   */
  isLoggedIn: any = false;

  /**
   * To call the API inside modal for editing the challenge details
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
   * @param DOCUMENT Document Injection
   */
  constructor(@Inject(DOCUMENT) document: any, private router: Router, private route: ActivatedRoute,
              private apiService: ApiService, private globalService: GlobalService,
              private challengeService: ChallengeService, public authService: AuthService,
              private endpointsService: EndpointsService, private meta: Meta) { }

  /**
   * Component on initialized
   */
  ngOnInit() {
    const SELF = this;
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.localRouter = this.router;
    this.globalService.scrollToTop();
    this.route.params.subscribe(params => {
      if (params['id']) {
        // this.fetchChallenge(params['id']);
        this.id = params['id'];
        this.challengeService.fetchChallenge(params['id']);
      }
    });
    this.challengeService.currentChallenge.subscribe(challenge => {
      this.challenge = challenge;
      // update meta tag
      SELF.meta.updateTag({
        property: 'og:title',
        content: SELF.challenge.title
      });
      SELF.meta.updateTag({
        property: 'og:description',
        content: SELF.challenge.short_description
      });
      SELF.meta.updateTag({
        property: 'og:image',
        content: SELF.challenge.image
      });
      SELF.meta.updateTag({
        property: 'og:url',
        content: document.location.href
      });
    });
    this.challengeService.currentStars.subscribe(stars => this.stars = stars);
    this.challengeService.currentParticipationStatus.subscribe(status => {
      this.isParticipated = status;
    });
    this.challengeService.isChallengeHost.subscribe(status => {
      this.isChallengeHost = status;
    });
    this.challengeService.currentChallengePublishState.subscribe(publishChallenge => {
      this.publishChallenge.state = publishChallenge.state;
      this.publishChallenge.icon = publishChallenge.icon;
    });
  }

  /**
   * Star click function.
   */
  starToggle(challengeId) {
    if (this.isLoggedIn) {
      this.challengeService.starToggle(challengeId);
    } else {
      this.globalService.showToast('error', 'Please login to star the challenge!', 5);
    }
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
        'published': isPublished
      });
      SELF.apiService.patchUrl(
        SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id),
        BODY
        ).subscribe(
        data => {
          if (isPublished) {
            this.publishChallenge.state = 'Published';
            this.publishChallenge.icon = 'fa fa-eye green-text';
          } else {
            this.publishChallenge.state = 'Not Published';
            this.publishChallenge.icon = 'fa fa-eye-slash red-text';
          }
          SELF.globalService.showToast('success', 'The challenge was successfully made ' + toggleChallengePublishState, 5);
        },
        err => {
          SELF.globalService.handleApiError(err, true);
          SELF.globalService.showToast('error', err);
        },
        () => console.log('PUBLISH-CHALLENGE-UPDATE-FINISHED')
      );
    };

    const PARAMS = {
      title: 'Make this challenge ' + toggleChallengePublishState + '?',
      content: '',
      confirm: 'Yes, I\'m sure',
      deny: 'No',
      confirmCallback: SELF.apiCall
    };
    SELF.globalService.showConfirm(PARAMS);
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
        () => console.log('EDIT-CHALLENGE-TITLE-FINISHED')
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

}
