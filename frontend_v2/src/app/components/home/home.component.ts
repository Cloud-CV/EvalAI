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
    { text: "At Motional we have been using EvalAI for all our nuScenes benchmark challenges. It is an easy-to-use open source platform on a non-profit basis. The team behind EvalAI consists of a number of accomplished academics and therefore we trust them to preserve the integrity of our test set annotations.", author: "Holger Caesar", org: "Motional", image: "https://www.nuscenes.org/public/images/team/Holger.jpg"},
    { text: "EvalAI has helped our competitions attract talented academic teams. EvalAI has also been responsive about adding new features.", author: "James Hayes", org: "ArgoAI", image: "https://faculty.cc.gatech.edu/~hays/headshots/2017c.jpg"},
    { text: "We used EvalAI for iGibson Challenge, the first visual navigation sim2real challenge in our community. EvalAI's flexible evaluation pipeline enables us to easily set up a rigorous workflow to test the submissions in simulation and on real robots. The workflow is easy for the participants as they just need to submit their solution with one command line and get back evaluation results. It is a great experience to create such a challenge and our participants totally enjoyed it! EvalAI has great potential to support robotics benchmarking on the cloud and provides opportunities to people who don't have access to the hardware.", author: "Fei Xia", org: "Stanford", image: "https://fxia22.github.io/assets/img/feixia.png"},
  ];

  /**
   * Selected testimonial text
   */
  testimonialBody = this.testimonials[this.selected]['text'];

  /**
   * Selected testimonial author
   */
  testimonialAuthor = this.testimonials[this.selected]['author'];

  /**
   * Selected testimonial orgName
   */
  testimonialOrg = this.testimonials[this.selected]['org'];

  /**
   * Selected testimonial author image
   */
  testimonialAuthorImage = this.testimonials[this.selected]['image'];

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
      scope.testimonialBody = scope.testimonials[scope.selected]['text'];
      scope.testimonialAuthor = scope.testimonials[scope.selected]['author'];
      scope.testimonialOrg = scope.testimonials[scope.selected]['org'];
      scope.testimonialAuthorImage = scope.testimonials[scope.selected]['image'];
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
