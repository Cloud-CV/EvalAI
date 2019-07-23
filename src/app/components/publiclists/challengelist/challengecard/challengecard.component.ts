import { Component, OnInit, Input } from '@angular/core';
import { GlobalService } from '../../../../services/global.service';
import { ApiService } from '../../../../services/api.service';
import { AuthService } from '../../../../services/auth.service';
import { ChallengeService } from '../../../../services/challenge.service';
import { Router, ActivatedRoute } from '@angular/router';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengecard',
  templateUrl: './challengecard.component.html',
  styleUrls: ['./challengecard.component.scss']
})
export class ChallengecardComponent implements OnInit {

  /**
   * Challenge object
   */
  @Input() challenge: object;

  /**
   * Start date string
   */
  startDate: any = '';

  /**
   * End date string
   */
  endDate: any = '';

  /**
   * Is challenge upcoming
   */
  isUpcoming = false;

  /**
   * Is Challenge ongoing
   */
  isOngoing = false;

  /**
   * Is it a past challenge
   */
  isPast = false;

  /**
   * Time remaining string
   */
  timeRemaining = '';

  /**
   * Is user logged in
   */
  isLoggedIn = false;

  /**
   * Tag list
   */
  tags = ['Aritificial Intelligence', 'Machine Learning'];

  /**
   * Challenge stars
   */
  stars = { 'count': 0, 'is_starred': false};

  /**
   * Challenge stars
   */
  routerPublic: Router;

  /**
   * My challenge route
   */
  myChallengesRoute = '/challenges/me';

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param authService  AuthService Injection.
   * @param apiService  ApiService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private globalService: GlobalService,
              private apiService: ApiService,
              private authService: AuthService,
              private challengeService: ChallengeService,
              private router: Router,
              private route: ActivatedRoute) { }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.routerPublic = this.router;
    this.preProcess();
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
  }

  /**
   * Called after onInit.
   */
  preProcess() {
    const TEMP = {};
    const PRESENT = new Date();
    const START_DATE = new Date(Date.parse(this.challenge['start_date']));
    const END_DATE = new Date(Date.parse(this.challenge['end_date']));
    this.checkType(START_DATE, END_DATE, PRESENT);
    this.startDate = this.globalService.formatDate12Hour(START_DATE);
    this.endDate = this.globalService.formatDate12Hour(END_DATE);
    this.fetchStars();

  }

  /**
   * Checks type of challenge (based on timing).
   * @param start  Start date
   * @param end  End date
   * @param now  Current date
   */
  checkType(start, end, now) {
    if (now > end) {
        this.isPast = true;
        this.timeRemaining = 'This challenge has ended.';
    } else if (now > start && now < end) {
      this.isOngoing = true;
      this.timeRemaining = this.globalService.getDateDifferenceString(now, end) + ' for the challenge to end.';
    } else if (now < start) {
      this.isUpcoming = true;
      this.timeRemaining = this.globalService.getDateDifferenceString(now, start) + ' for the challenge to begin.';
    }
  }

  /**
   * Fetch Stars for the current challenge card.
   */
  fetchStars() {
    this.challengeService.fetchStars(this.challenge['id'], (data) => {
      this.stars = data;
    });
  }

  /**
   * Toggle stars for the current challenge card.
   */
  starToggle() {
    if (this.isLoggedIn) {
      this.challengeService.starToggle(this.challenge['id'], (data, self) => {
        self.stars = data;
      }, this);
    }
  }

  /**
   * Challenge card is clicked (redirect).
   */
  challengeClicked() {
    this.router.navigate(['/challenge', this.challenge['id']]);
  }

  /**
   * Participate in the current challenge card (redirect).
   */
  participateInChallenge() {
    this.router.navigate(['/challenge', this.challenge['id'], 'participate']);
  }
}
