import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { ChallengeService } from '../../services/challenge.service';

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
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  GlobalService Injection.
   * @param authService  AuthService Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  Router Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private router: Router, private route: ActivatedRoute,
              private apiService: ApiService, private globalService: GlobalService,
              private challengeService: ChallengeService, private authService: AuthService) { }

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
    this.challengeService.currentChallenge.subscribe(challenge => this.challenge = challenge);
    this.challengeService.currentStars.subscribe(stars => this.stars = stars);
    this.challengeService.currentParticipationStatus.subscribe(status => {
      this.isParticipated = status;
    });
  }

  /**
   * Star click function.
   */
  starToggle(challengeId) {
    if (this.isLoggedIn) {
      this.challengeService.starToggle(challengeId);
    }
  }
}
