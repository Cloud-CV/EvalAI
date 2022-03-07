import { Component, Inject, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { Meta } from '@angular/platform-browser';
import { DOCUMENT } from '@angular/common';

// import services
import { AuthService } from '../../services/auth.service';
import { GlobalService } from '../../services/global.service';
import { ChallengeService } from '../../services/challenge.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-challenge',
  templateUrl: './challenge.component.html',
  styleUrls: ['./challenge.component.scss'],
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
   * Is challenge approved by admin
   */  
  isApprovedByAdmin = false;

  /**
   * Is participated in Challenge
   */
  isParticipated = false;

  /**
   * Is Forum enabled in Challenge
   */
  isForumEnabled: boolean;

  /**
   * Forum Url of Challenge
   */
  forumURL: any;

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
   * Is past challenge
   */
  isPast: any = false;

  /**
   * Challenge phases
   */
  phases: any = [];

  /**
   * Constructor.
   * @param router  Router Injection.
   * @param route  ActivatedRoute Injection.
   * @param globalService  GlobalService Injection.
   * @param challengeService  ChallengeService Injection.
   * @param authService  AuthService Injection.
   */
  constructor(
    @Inject(DOCUMENT) document: any,
    private router: Router,
    private route: ActivatedRoute,
    private globalService: GlobalService,
    private challengeService: ChallengeService,
    public authService: AuthService,
    private meta: Meta
  ) {}

  /**
   * Component on initialized
   */
  ngOnInit() {
    this.globalService.startLoader('');
    const SELF = this;
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.localRouter = this.router;
    this.globalService.scrollToTop();
    this.route.params.subscribe((params) => {
      if (params['id']) {
        // this.fetchChallenge(params['id']);
        this.id = params['id'];
        this.challengeService.fetchChallenge(params['id']);
      }
    });
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
      this.isForumEnabled = challenge.enable_forum;
      this.forumURL = challenge.forum_url;
      this.isApprovedByAdmin = challenge.approved_by_admin;
      this.isPast = this.isPastChallenge();
      // update meta tag
      SELF.meta.updateTag({
        property: 'og:title',
        content: SELF.challenge.title,
      });
      SELF.meta.updateTag({
        property: 'og:description',
        content: SELF.challenge.short_description,
      });
      SELF.meta.updateTag({
        property: 'og:image',
        content: SELF.challenge.image,
      });
      SELF.meta.updateTag({
        property: 'og:url',
        content: document.location.href,
      });
    });
    this.challengeService.currentPhases.subscribe((phases) => {
      this.phases = phases;
    });
    this.challengeService.currentStars.subscribe((stars) => (this.stars = stars));
    this.challengeService.currentParticipationStatus.subscribe((status) => {
      this.isParticipated = status;
    });
    this.challengeService.isChallengeHost.subscribe((status) => {
      this.isChallengeHost = status;
    });
    this.globalService.stopLoader();
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

  isPastChallenge() {
    const PRESENT = new Date();
    const START_DATE = new Date(Date.parse(this.challenge['start_date']));
    const END_DATE = new Date(Date.parse(this.challenge['end_date']));
    return (PRESENT > END_DATE);
  }
}
