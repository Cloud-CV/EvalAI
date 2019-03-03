import { Component, OnInit, OnDestroy, ChangeDetectorRef, Inject, HostListener } from '@angular/core';
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { RouterModule, Router, ActivatedRoute, NavigationEnd } from '@angular/router';
import { DOCUMENT } from '@angular/common';

/**
 * Component Class
 */
@Component({
  selector: 'app-header-static',
  templateUrl: './header-static.component.html',
  styleUrls: ['./header-static.component.scss']
})
export class HeaderStaticComponent implements OnInit, OnDestroy {

  /**
   * Header white flag
   */
  headerWhite = false;

  /**
   * Header is transparent on these URLs
   */
  transparentHeaderUrls = ['', '/'];

  /**
   * Is router at '/'
   */
  atHome = true;

  /**
   * Scroll position
   */
  scrolledState = false;

  /**
   * Is header menu expanded
   */
  isMenuExpanded = true;

  /**
   * Global Service subscription
   */
  globalServiceSubscription: any;

  /**
   * Authentication Service subscription
   */
  authServiceSubscription: any;

  /**
   * Current Authentication state
   */
  authState: any;

  /**
   * Inner width
   */
  public innerWidth: any;

  /**
   * Constructor.
   * @param document  Window document Injection.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param authService  AuthService Injection.
   * @param apiService  ApiService Injection.
   * @param ref  Angular Change Detector Injection.
   */
  constructor(private globalService: GlobalService,
              private route: ActivatedRoute,
              private router: Router,
              private ref: ChangeDetectorRef,
              private authService: AuthService,
              @Inject(DOCUMENT) private document: Document) {
                 this.authState = authService.authState;
              }

  /**
   * Update View Elements (called after onInit).
   */
  updateElements() {
    this.headerWhite = false;
    this.atHome = true;

    if (!this.transparentHeaderUrls.includes(this.router.url)) {
      this.atHome = false;
      this.headerWhite = true;
    }

    this.globalServiceSubscription = this.globalService.currentScrolledState.subscribe(scrolledState => {
      this.headerWhite = scrolledState || !this.atHome;
      this.scrolledState = scrolledState;
    });
  }

  /**
   * Component on intialized.
   */
  ngOnInit() {
    this.updateElements();
    this.innerWidth = window.innerWidth;
    if (this.innerWidth <= 810) {
      this.isMenuExpanded = false;
    }
    this.authServiceSubscription = this.authService.change.subscribe((authState) => {
      this.authState = authState;
    });
  }
  @HostListener('window:resize', ['$event'])
  onResize(event) {
    this.innerWidth = window.innerWidth;
    if (this.innerWidth <= 810) {
      this.isMenuExpanded = false;
    }
  }

  /**
   * Redirect to home if not at home (/).
   */
  sendMeHome() {
    this.atHome = true;
    this.headerWhite = false;
    this.ref.detectChanges();
    this.router.navigate(['']);
  }

  /**
   * Navigate to URL.
   * @param path  destination URL
   */
  navigateTo(path) {
    this.isMenuExpanded = false;
    if (path === '/auth/login') {
      this.globalService.storeData('redirect', path);
    }
    this.router.navigate([path]);
  }

  /**
   * Component on destroyed.
   */
  ngOnDestroy() {
    if (this.globalServiceSubscription) {
      this.globalServiceSubscription.unsubscribe();
    }
    if (this.authServiceSubscription) {
      this.authServiceSubscription.unsubscribe();
    }
  }

  /**
   * Perform Log-out.
   */
  logOut() {
    this.authService.logOut();
  }

  /**
   * Flag for expanding navigation menu on the header.
   */
  menuExpander() {
    this.isMenuExpanded = !this.isMenuExpanded;
  }

}
