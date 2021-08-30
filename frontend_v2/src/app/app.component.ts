import { mergeMap, map, filter } from 'rxjs/operators';
import { Component, OnInit, OnDestroy, HostListener, Inject } from '@angular/core';
import { GlobalService } from './services/global.service';
import { AuthService } from './services/auth.service';
import { Router, NavigationEnd, ActivatedRoute, Event } from '@angular/router';
import { DOCUMENT } from '@angular/common';
import { Title } from '@angular/platform-browser';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent implements OnInit, OnDestroy {
  private scrolledState = false;
  isLoading = false;
  confirmParams = { isConfirming: false };
  modalParams = { isModalVisible: false };
  editPhaseModalParams = { isEditPhaseModalVisible: false };
  termsAndConditionsModalParams = { isTermsAndConditionsModalVisible: false };
  globalServiceSubscription: any;
  globalLogoutTrigger: any;
  globalLoadingSubscription: any;
  globalConfirmSubscription: any;
  globalModalSubscription: any;
  globalEditPhaseModalSubscription: any;
  globalTermsAndConditionsModalSubscription: any;
  globalServiceSubscriptionScrollTop: any;
  currentRoutePath: any;

  /**
   * Constructor.
   * @param document  Window document injection
   * @param router  Router Injection.
   * @param activatedRoute  ActivatedRoute Injection.
   * @param titleService  Title from angular's platform-browser Injection.
   * @param globalService  GlobalService Injection.
   * @param authService  AuthService Injection.
   */
  constructor(
    @Inject(DOCUMENT) private document: Document,
    public router: Router,
    public activatedRoute: ActivatedRoute,
    public titleService: Title,
    private globalService: GlobalService,
    private authService: AuthService
  ) {}

  /**
   * Scroll event listener.
   */
  @HostListener('window:scroll', [])
  onWindowScroll(): void {
    if (this.document.documentElement.scrollTop > 50) {
      if (this.scrolledState === false) {
        this.globalService.scrolledStateChange(true);
        document.getElementById('up-arrow').style.display = 'block';
      }
    } else {
      if (this.scrolledState === true) {
        this.globalService.scrolledStateChange(false);
        document.getElementById('up-arrow').style.display = 'none';
      }
    }
  }

  /**
   * Component when initialized. Subscribes to observables
   */
  ngOnInit() {
    this.router.events.subscribe((event: Event) => {
      if (event instanceof NavigationEnd) {
        this.currentRoutePath = event.url; // current url path
      }
    });
    const SELF = this;
    this.globalServiceSubscription = this.globalService.currentScrolledState.subscribe((scrolledState) => {
      this.scrolledState = scrolledState;
    });
    this.globalLogoutTrigger = this.globalService.logout.subscribe(() => {
      this.authService.logOut();
    });
    this.globalLoadingSubscription = this.globalService.currentisLoading.subscribe((isLoading) => {
      setTimeout(() => {
        this.isLoading = isLoading;
      }, 0);
    });
    this.globalConfirmSubscription = this.globalService.currentConfirmParams.subscribe((params) => {
      setTimeout(() => {
        this.confirmParams = params;
      }, 0);
    });
    this.globalModalSubscription = this.globalService.currentModalParams.subscribe((params) => {
      setTimeout(() => {
        this.modalParams = params;
      }, 0);
    });

    this.globalEditPhaseModalSubscription = this.globalService.editPhaseModalParams.subscribe((params) => {
      this.editPhaseModalParams = params;
    });

    this.globalTermsAndConditionsModalSubscription = this.globalService.termsAndConditionsModalParams.subscribe(
      (params) => {
        this.termsAndConditionsModalParams = params;
      }
    );

    this.globalServiceSubscriptionScrollTop = this.globalService.scrolltop.subscribe(() => {
      SELF.document.body.scrollTop = SELF.document.documentElement.scrollTop = 0;
    });

    // set page title form routes data
    this.router.events
      .pipe(
        // filter for navigation end
        filter((event) => event instanceof NavigationEnd),
        // check it with current activated route
        map(() => this.activatedRoute),
        // loop state routes to get the last activated route, first child and return it
        map((route) => {
          while (route.firstChild) {
            route = route.firstChild;
          }
          return route;
        }),
        // filter for primary route
        filter((route) => route.outlet === 'primary'),
        mergeMap((route) => route.data)
      )
      // set platform based title service
      .subscribe((event) => this.titleService.setTitle(event['title']));
  }

  /**
   * Component On-Destroy. (Unsubscribes from subscriptions)
   */
  ngOnDestroy() {
    if (this.globalServiceSubscription) {
      this.globalServiceSubscription.unsubscribe();
    }
    if (this.globalLogoutTrigger) {
      this.globalLogoutTrigger.unsubscribe();
    }
    if (this.globalLoadingSubscription) {
      this.globalLoadingSubscription.unsubscribe();
    }
    if (this.globalServiceSubscriptionScrollTop) {
      this.globalServiceSubscriptionScrollTop.unsubscribe();
    }
  }

  scrollUp() {
    document.body.scrollIntoView({ behavior: 'smooth' });
  }
}
