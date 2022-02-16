import { Component, OnDestroy, OnInit, ViewChildren, QueryList, AfterViewInit, Inject } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { EndpointsService } from '../../services/endpoints.service';
import { AuthService } from '../../services/auth.service';
import { GlobalService } from '../../services/global.service';
import { Router } from '@angular/router';
import { InputComponent } from '../../components/utility/input/input.component';
import { DOCUMENT } from '@angular/common';

/**
 * Component Class
 */
@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
})
export class HomeComponent implements OnInit, AfterViewInit, OnDestroy {
  challengeCreateRoute = '/challenge-create';
  authRoute = '/auth/login';
  public user = {};
  public challengeList = [];

  /**
   * Selected testimonial index
   */
  selected = 0;

  /**
   * Placeholder text Lorem Ipsum
   */
  ipsum: any =
    'Lorem ipsum dolor sit amet,\
  consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.';

  /**
   * Sample testimonials till the API comes up
   */
  testimonials = [
    { text: '1-' + this.ipsum, author: 'Lorem', org: 'Georgia Tech', image: '' },
    { text: '2-' + this.ipsum, author: 'Octopus', org: 'Google', image: '' },
    { text: '3-' + this.ipsum, author: 'Penguin', org: 'Facebook', image: '' },
  ];

  /**
   * Selected testimonial text
   */
  testimonialbody = this.testimonials[this.selected]['text'];

  /**
   * Selected testimonial author
   */
  testimonialauthor = this.testimonials[this.selected]['author'];

  /**
   * Selected testimonial orgName
   */
  testimonialorg = this.testimonials[this.selected]['org'];

  /**
   * Subscribe Form
   */

  SUBSCRIBE_FORM: any = {};
  subscribeForm = 'formgroup';

  @ViewChildren('formgroup')
  components: QueryList<InputComponent>;

  authServiceSubscription: any;

  /**
   * Constructor.
   * @param apiService  ApiServiceInjection
   * @param endpointService  EndPointServiceInjection.
   * @param authService  AuthServiceInjection.
   * @param globalService  GlobalService Injection.
   * @param router  Router Injection.
   */

  constructor(
    private apiService: ApiService,
    private endpointService: EndpointsService,
    private authService: AuthService,
    private globalService: GlobalService,
    private router: Router,
    @Inject(DOCUMENT) private document: Document
  ) {}

  ngOnInit() {
    this.init();
    this.getChallenge();
  }

  /**
   * Set SUBSCRIBE_FORM to this.components after view initialization
   */
  ngAfterViewInit() {
    this.SUBSCRIBE_FORM[this.subscribeForm] = this.components;
    (<any>window).twttr.widgets.load();
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
      (response) => {
        this.challengeList = response.results.slice(0, 4);
      },
      (err) => {
        this.globalService.handleApiError(err);
      },
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
      (response) => {
        // Success Message in response.message
        setTimeout(() => self.globalService.showToast('success', response.message, 5), 1000);
      },
      // Show Form Error on Failure
      (err) => {
        if (err.status === 400) {
          setTimeout(() => self.globalService.showToast('info', err.error.message, 5), 1000);
        } else if (err.error.message) {
          setTimeout(() => self.globalService.showToast('error', err.error.message, 5), 1000);
        } else {
          self.globalService.handleApiError(err);
        }
      },
      () => {}
    );
  }

  /**
   * Right arrow clicked
   */
  testimonialRight() {
    this.selected = this.selected + 1;
    if (this.selected >= this.testimonials.length) {
      this.selected = 0;
    }
  }

  /**
   * left arrow clicked
   */
  testimonialLeft() {
    this.selected = this.selected - 1;
    if (this.selected < 0) {
      this.selected = this.testimonials.length - 1;
    }
  }

  /**
   * Testimonials navigated
   */
  testimonialNavigate(direction = 'left') {
    const a = this.document.getElementsByClassName('testimonial-body')[0];
    const b = this.document.getElementsByClassName('testimonial-author')[0];
    const c = this.document.getElementsByClassName('testimonial-quotes')[0];
    const d = this.document.getElementsByClassName('testimonial-org')[0];
    if (direction === 'left') {
      this.testimonialLeft();
    } else {
      this.testimonialRight();
    }
    this.flyOut(a, direction, this);
    this.disappearAppear(a, this);
    this.disappearAppear(b, this);
    this.disappearAppear(c, this);
    this.disappearAppear(d, this);
  }

  /**
   * Fly out animation
   */
  flyOut = (element, direction, scope) => {
    const temp = 15;
    setTimeout(function () {
      scope.testimonialbody = scope.testimonials[scope.selected]['text'];
      scope.testimonialauthor = scope.testimonials[scope.selected]['author'];
      scope.testimonialorg = scope.testimonials[scope.selected]['org'];
    }, 1000);
  };

  /**
   * Disappear animation
   */
  disappearAppearRecursive = (element, temp) => {
    const x = temp - 0.01;
    if (x >= 0) {
      (function (scope) {
        setTimeout(function () {
          element.style.opacity = x + '';
          scope.disappearAppearRecursive(element, x);
        }, 5);
      })(this);
    }
  };

  /**
   * Disappear animation wrapper
   */
  disappearAppear = (element, scope) => {
    const temp = 1.0;
    this.disappearAppearRecursive(element, temp);
    setTimeout(function () {
      element.style.opacity = '1';
    }, 1000);
  };

  ngOnDestroy(): void {
    if (this.authServiceSubscription) {
      this.authServiceSubscription.unsubscribe();
    }
  }
}
