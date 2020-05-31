import {Component, OnDestroy, OnInit, ViewChildren, QueryList, AfterViewInit} from '@angular/core';
import {ApiService} from '../../services/api.service';
import {EndpointsService} from '../../services/endpoints.service';
import {AuthService} from '../../services/auth.service';
import {GlobalService} from '../../services/global.service';
import {BehaviorSubject} from 'rxjs';
import {Router} from '@angular/router';
import { InputComponent } from '../../components/utility/input/input.component';

/**
 * Component Class
 */
@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})

export class HomeComponent implements OnInit, AfterViewInit, OnDestroy {
  challengeCreateRoute = '/challenge-create';
  authRoute = '/auth/login';
  public user = {};
  public challengeList = [];

 /**
 * Subscribe Form
 */

  SUBSCRIBE_FORM: any = {};
  subscribeForm = 'formgroup';

  @ViewChildren('formgroup')
  components: QueryList<InputComponent>;


  authServiceSubscription: any;
  constructor(private apiService: ApiService, private endpointService: EndpointsService, private authService: AuthService,
              private globalService: GlobalService, private router: Router) { }

  ngOnInit() {
    this.init();
    this.getChallenge();
  }

  /**
   * Set SUBSCRIBE_FORM to this.components after view initialization
   */
  ngAfterViewInit() {
    this.SUBSCRIBE_FORM[this.subscribeForm] = this.components;
  }

  init() {
    this.authServiceSubscription = this.authService.change.subscribe((authState) => {
      if (authState.isLoggedIn) {
        this.user = authState;
      }
    });
  }

  getChallenge() {
    this.apiService.getUrl(this.endpointService.featuredChallengesURL()).subscribe(
      response => {
        this.challengeList = response.results;
      },
      err => { this.globalService.handleApiError(err); },
      () => {}
    );

  }

  hostChallenge() {
    if (this.authService.isAuth) {
      this.router.navigate([this.challengeCreateRoute]);
    } else {
      this.router.navigate([this.authRoute]);
    }
  }

  /**
   * Form submit function (Called after validation).
   * @param self context value of this
   * Validate Subscribe Form
   */
  formValidate(formname) {
    this.globalService.formValidate(this.SUBSCRIBE_FORM[this.subscribeForm], this.subscribe, this);
  }

  /**
   * Subscribe function - POST email to Subscribe URL for evaluation
   */
  subscribe(self) {
    const SUBSCRIBE_BODY = JSON.stringify({
      email: self.globalService.formValueForLabel(self.SUBSCRIBE_FORM[self.subscribeForm], 'email'),
    });
    self.apiService.postUrl(self.endpointService.subscribeURL(), SUBSCRIBE_BODY).subscribe(
      response => {
        // Success Message in response.message
        setTimeout(() => self.globalService.showToast('success', response.message, 5), 1000);
      },
      // Show Form Error on Failure
      err => {
        if (err.error.message) {
          setTimeout(() => self.globalService.showToast('error', err.error.message, 5), 1000);
        } else {
        self.globalService.handleApiError(err);
        }
      },
      () => {}
    );
  }

  ngOnDestroy(): void {
    if (this.authServiceSubscription) {
      this.authServiceSubscription.unsubscribe();
    }
  }
}
