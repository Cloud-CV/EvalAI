import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../../services/auth.service';
import { ChallengeService } from '../../../services/challenge.service';
import { GlobalService } from '../../../services/global.service';
import { Router, ActivatedRoute } from '@angular/router';
import { NGXLogger } from 'ngx-logger';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengeparticipate',
  templateUrl: './challengeparticipate.component.html',
  styleUrls: ['./challengeparticipate.component.scss']
})
export class ChallengeparticipateComponent implements OnInit {

  /**
   * Is user logged in
   */
  isLoggedIn = false;

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Router's public instance
   */
  routerPublic: any;

  /**
   * Is user a participant
   */
  isParticipated: any;

  /**
   * Is challenge active
   */
  isActive: any;

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param authService  AuthService Injection.
   * @param globalService  GlobalService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private authService: AuthService, private router: Router, private route: ActivatedRoute,
              private challengeService: ChallengeService, private globalService: GlobalService,
              private logger: NGXLogger) { }

  /**
   * Component on initialized
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.routerPublic = this.router;
    this.challengeService.currentChallenge.subscribe(challenge => {
      this.challenge = challenge;
      this.isActive = this.challenge['is_active'];
    });
    this.challengeService.currentParticipationStatus.subscribe(status => {
      this.isParticipated = status;
      if (status) {
        const REDIRECT = this.globalService.getData(this.globalService.redirectStorageKey);
        if (REDIRECT && REDIRECT['path']) {
          this.globalService.deleteData(this.globalService.redirectStorageKey);
          this.router.navigate([REDIRECT['path']]);
        } else {
          this.logger.info('navigating to /submit', status);
          this.router.navigate(['../submit'], {relativeTo: this.route});
        }
      }
    });
  }

}
