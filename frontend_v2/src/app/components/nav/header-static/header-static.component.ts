import {
  Component,
  OnInit,
  OnDestroy,
  ChangeDetectorRef,
  Inject,
  HostListener,
  ViewChild,
  ElementRef,
} from '@angular/core';
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { filter } from "rxjs/internal/operators";
import { Router, NavigationEnd } from '@angular/router';
import { DOCUMENT } from '@angular/common';

/**
 * Component Class
 */
@Component({
  selector: 'app-header-static',
  templateUrl: './header-static.component.html',
  styleUrls: ['./header-static.component.scss'],
})
export class HeaderStaticComponent implements OnInit, OnDestroy {
  user = { username: '' };

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
   * Is user Logged in
   */
  isLoggedIn: any = false;

  /**
   * Current name of tab which needs to be active
   */
  tabHighlight: string = "allChallenges";

  /**
   * Returns true if the string is not a number
   */
  isChallengeComponent : boolean = false;

  /**
   * Inner width
   */
  public innerWidth: any;

  @ViewChild('navContainer') navContainer: ElementRef;

  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   * @param router  Router Injection.
   * @param ref  Angular Change Detector Injection.
   * @param authService  AuthService Injection.
   * @param document  Window document Injection.
   */
  constructor(
    private globalService: GlobalService,
    private router: Router,
    private ref: ChangeDetectorRef,
    public authService: AuthService,
    @Inject(DOCUMENT) private document: Document
  ) {
      this.authState = authService.authState;
  }

  /**
   * Update View Elements (called after onInit).
   */
  updateElements() {
    this.atHome = true;
    this.globalServiceSubscription = this.globalService.currentScrolledState.subscribe((scrolledState) => {
      this.scrolledState = scrolledState;
    });
  }

  /**
   * Component on intialized.
   */
  ngOnInit() {
    this.updateElements();
    this.checkInnerWidth();

    this.router.events
    .pipe(filter(event => event instanceof NavigationEnd))
    .subscribe((event) => {
      if(event) {
          if(this.router.url.split('/')[length] == "all") {
            this.tabHighlight = "allChallenges";
            this.globalService.changeTabActiveStatus("allChallenges");
          }
          else if(this.router.url.split('/')[1] == "profile") {
            this.tabHighlight = "profile";
            this.globalService.changeTabActiveStatus("profile");
          }
      }
    });
    this.isChallengeComponent = isNaN(parseInt(this.router.url.split('/')[length]));
    
    this.globalService.nameTabHighlight.subscribe((tabHighlight) => {
      this.tabHighlight = tabHighlight;
    });

    this.authServiceSubscription = this.authService.change.subscribe((authState) => {
      this.authState = authState;
      if (this.authService.isLoggedIn()) {
        this.isLoggedIn = true;
      }
      if (this.authState.isLoggedIn) {
        this.user = this.authState;
      }
    });
  }

  @HostListener('window:resize', ['$event'])
  onResize(event) {
    this.checkInnerWidth();
  }

  /**
   * Redirect to home if not at home (/).
   */
  sendMeHome() {
    this.atHome = true;
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

  checkInnerWidth() {
    this.innerWidth = window.innerWidth;
    if (this.innerWidth > 810) {
      this.isMenuExpanded = true;
    }
  }
}
