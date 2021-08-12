import { Component, HostListener, Inject, OnInit } from '@angular/core';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { Router } from '@angular/router';
import { DOCUMENT } from '@angular/common';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengelist',
  templateUrl: './challengelist.component.html',
  styleUrls: ['./challengelist.component.scss'],
})
export class ChallengelistComponent implements OnInit {
  /**
   * Filter toggle flag
   */
  isUpcomingChecked = true;

  /**
   * Filter toggle flag
   */
  isOngoingChecked = true;

  /**
   * Filter toggle flag
   */
  isPastChecked = true;

  /**
   * Upcoming challenges list
   */
  upcomingChallenges = [];

  /**
   * Ongoing challenges list
   */
  ongoingChallenges = [];

  /**
   * Past challeges list
   */
  pastChallenges = [];

  /**
   * Unapproved challeges list
   */
  unapprovedChallengeList = [];

  /**
   * API common path
   */
  apiPathCommon = 'challenges/challenge/';

  /**
   * participated challenges API common path
   */
  newApiPathCommon = 'challenges/challenges/';

  /**
   * Host teams API common path
   */
  hostTeamsapiPathCommon = 'hosts/challenge_host_team';

  /**
   * API path mapping
   */
  apiPathMapping = {
    isUpcomingChecked: this.apiPathCommon + 'future',
    isOngoingChecked: this.apiPathCommon + 'present',
    isPastChecked: this.apiPathCommon + 'past',
  };

  /**
   * API path mapping
   */
  newApiPathMapping = {
    isOngoingChecked: this.newApiPathCommon + 'participated/' + 'present/',
    isPastChecked: this.newApiPathCommon + 'participated/' + 'past/',
  };

  /**
   * List of filtered challenges
   */
  filteredChallenges = [];

  /**
   * List of filtered ongoing challenges
   */
  filteredOngoingChallenges = [];

  /**
   * List of filtered upcoming challenges
   */
  filteredUpcomingChallenges = [];

  /**
   * List of filtered past challenges
   */
  filteredPastChallenges = [];

  /**
   * List of filtered-further challenges
   */
  filteredChallengesView = [];

  /**
   * Team list
   */
  allTeams = [];

  /**
   * Display more frames of teams
   */
  seeMore = 1;

  /**
   * Frame size
   */
  windowSize = 10;

  /**
   * Auth service public instance
   */
  authServicePublic: AuthService;

  /**
   * Router public instance
   */
  routerPublic: Router;

  /**
   * Is user Logged in
   */
  isLoggedIn: any = false;

  /**
   * Is scroll button visible
   */
  isScrollbtnVisible = false;

  /**
   * Authentication Service subscription
   */
  authServiceSubscription: any;

  /**
   * All challenges common route path
   */
  allChallengesRoutePathCommon = '/challenges/all';

  /**
   * My challenges common route path
   */
  myChallengesRoutePathCommon = '/challenges/me';

  /**
   * My participated challenges common route path
   */
  myParticipatedChallengesRoutePathCommon = '/challenges/participated';

  /**
   * Host teams common route path
   */
  hostTeamsRoutePathCommon = '/teams/hosts';

  /**
   * Challenge common path
   */
  challengeRoutePathCommon = '/challenge';

  /**
   * Auth common route path
   */
  authRoutePathCommon = '/auth/';

  /**
   * Constructor.
   * @param apiService  ApiService Injection.
   * @param authService  AuthService Injection.
   * @param globalService  GlobalService Injection.
   * @param endpointsService  EndpointsService Injection.
   * @param router  Router Injection.
   * @param document
   */
  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private globalService: GlobalService,
    private endpointsService: EndpointsService,
    private router: Router,
    @Inject(DOCUMENT) private document
  ) {}

  /**
   * Component on intialized.
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }

    this.authServiceSubscription = this.authService.change.subscribe((authState) => {
      this.isLoggedIn = authState.isLoggedIn;
      if (!authState.isLoggedIn && this.router.url === this.myChallengesRoutePathCommon) {
        this.router.navigate([`${this.authRoutePathCommon}login`]);
      } else if (!authState.isLoggedIn && this.router.url === this.myParticipatedChallengesRoutePathCommon) {
        this.router.navigate([`${this.authRoutePathCommon}login`]);
      }
    });

    if (this.router.url === this.allChallengesRoutePathCommon) {
      this.fetchChallenges();
    } else if (this.router.url === this.myChallengesRoutePathCommon && this.authService.isLoggedIn()) {
      this.fetchMyTeams();
    } else if (this.router.url === this.myParticipatedChallengesRoutePathCommon && this.authService.isLoggedIn()) {
      this.fetchMyParticipatedChallenges();
    }

    this.authServicePublic = this.authService;
    this.routerPublic = this.router;
  }

  /**
   * Listener for page scroll event
   */
  @HostListener('window:scroll', [])
  onWindowScroll(): void {
    if(this.document.getElementById('ongoing-challenges')) {
      const RECT = this.document.getElementById('ongoing-challenges').getBoundingClientRect();
      this.isScrollbtnVisible = RECT.top < 0;
    }
  }

  /**
   * Fetch teams function.
   */
  fetchMyTeams() {
    this.fetchTeams(this.hostTeamsapiPathCommon);
  }

  /**
   * Fetch participated challenges function.
   * @param filter  selected filter
   * @param callback  callback function
   */
  fetchMyParticipatedChallenges(filter = null, callback = null) {
    const SELF = this;
    if (!filter) {
      const ALL_PATHS = Object.values(SELF.newApiPathMapping);
      const ALL_KEYS = Object.keys(SELF.newApiPathMapping);
      for (let i = 0; i < ALL_PATHS.length; i++) {
        if (SELF[ALL_KEYS[i]]) {
          SELF.fetchParticipatedChallengesFromApi(ALL_PATHS[i], callback);
        }
      }
    } else {
      SELF.fetchParticipatedChallengesFromApi(SELF.newApiPathMapping[filter], callback);
    }
  }

  /**
   * Toggle upcoming/past/ongoing filters.
   * @param filter  selected filter
   */
  toggleFilter(filter) {
    this[filter] = !this[filter];
    if (this[filter]) {
      this.fetchChallenges(filter);
    } else {
      this.upcomingChallenges = filter === 'isUpcomingChecked' ? [] : this.upcomingChallenges;
      this.ongoingChallenges = filter === 'isOngoingChecked' ? [] : this.ongoingChallenges;
      this.pastChallenges = filter === 'isPastChecked' ? [] : this.pastChallenges;
      this.filteredChallenges = this.upcomingChallenges.concat(this.ongoingChallenges, this.pastChallenges);
      this.filteredOngoingChallenges = this.ongoingChallenges;
      this.filteredUpcomingChallenges = this.upcomingChallenges;
      this.filteredPastChallenges = this.pastChallenges;
      this.updateChallengesView(true);
    }
  }

  /**
   * Show more results.
   */
  seeMoreClicked() {
    this.seeMore = this.seeMore + 1;
    this.updateChallengesView(false);
  }

  /**
   * Update challenges view (called after fetching challenges from API).
   * @param reset  reset flag for hiding/showing more results
   */
  updateChallengesView(reset) {
    if (reset) {
      this.seeMore = 1;
    }
    this.filterChallengesByTeams();
    this.filteredChallengesView = this.filteredChallenges.slice(0, this.seeMore * this.windowSize);
  }

  /**
   * Filtering challenges by teams
   */
  filterChallengesByTeams() {
    if (this.router.url === this.myChallengesRoutePathCommon && this.authService.isLoggedIn()) {
      this.filteredChallenges = this.filteredChallenges.filter(
        (v, i, a) => this.allTeams.indexOf(v['creator']['id']) > -1
      );
      this.filteredOngoingChallenges = this.filteredOngoingChallenges.filter(
        (v, i, a) => this.allTeams.indexOf(v['creator']['id']) > -1
      );
      this.filteredUpcomingChallenges = this.filteredUpcomingChallenges.filter(
        (v, i, a) => this.allTeams.indexOf(v['creator']['id']) > -1
      );
      this.filteredPastChallenges = this.filteredPastChallenges.filter(
        (v, i, a) => this.allTeams.indexOf(v['creator']['id']) > -1
      );
    }
  }

  /**
   * Fetch teams function.
   * @param path  teams fetch URL
   */
  fetchTeams(path) {
    const SELF = this;
    SELF.filteredChallenges = [];
    this.apiService.getUrl(path, true, false).subscribe(
      (data) => {
        if (data['results']) {
          const TEAMS = data['results'].map((item) => item['id']);
          SELF.allTeams = SELF.allTeams.concat(TEAMS);
          SELF.allTeams = SELF.allTeams.filter((v, i, a) => a.indexOf(v) === i);
          SELF.allTeams.forEach((team) => {
            SELF.fetchUnapprovedChallengesFromApi(team);
          });
          SELF.fetchChallenges();
        }
      },
      (err) => {
        if (err.status === 403) {
          this.router.navigate(['permission-denied']);
        }
        SELF.globalService.handleApiError(err, false);
      },
      () => {}
    );
  }

  /**
   * Fetch Challenges function.
   * @param filter  selected filter
   * @param callback  callback function
   */
  fetchChallenges(filter = null, callback = null) {
    if (!filter) {
      const ALL_PATHS = Object.values(this.apiPathMapping);
      const ALL_KEYS = Object.keys(this.apiPathMapping);
      for (let i = 0; i < ALL_PATHS.length; i++) {
        if (this[ALL_KEYS[i]]) {
          this.fetchChallengesFromApi(ALL_PATHS[i], callback);
        }
      }
    } else {
      this.fetchChallengesFromApi(this.apiPathMapping[filter], callback);
    }
  }

  /**
   * Fetch challenges from backend.
   * @param path  Challenge fetch URL
   * @param callback  Callback Function.
   */
  fetchChallengesFromApi(path, callback = null) {
    const SELF = this;
    SELF.apiService.getUrl(path, true, false).subscribe(
      (data) => {
        if (path.endsWith('future')) {
          SELF.upcomingChallenges = data['results'];
        } else if (path.endsWith('present')) {
          SELF.ongoingChallenges = data['results'];
        } else if (path.endsWith('past')) {
          SELF.pastChallenges = data['results'];
        }
        SELF.filteredChallenges = SELF.upcomingChallenges.concat(SELF.ongoingChallenges, SELF.pastChallenges);
        SELF.filteredOngoingChallenges = SELF.ongoingChallenges;
        SELF.filteredUpcomingChallenges = SELF.upcomingChallenges;
        SELF.filteredPastChallenges = SELF.pastChallenges;
        this.updateChallengesView(true);
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );
  }

  /**
   * Fetch participated challenges from backend.
   * @param path  Challenge fetch URL
   * @param callback  Callback Function.
   */
  fetchParticipatedChallengesFromApi(path, callback = null) {
    const SELF = this;
    SELF.apiService.getUrl(path, true, false).subscribe(
      (data) => {
        if (path.endsWith('present/')) {
          SELF.ongoingChallenges = data['results'];
        } else if (path.endsWith('past/')) {
          SELF.pastChallenges = data['results'];
        }
        SELF.filteredChallenges = SELF.upcomingChallenges.concat(SELF.ongoingChallenges, SELF.pastChallenges);
        SELF.filteredOngoingChallenges = SELF.ongoingChallenges;
        SELF.filteredPastChallenges = SELF.pastChallenges;
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );
  }

  fetchUnapprovedChallengesFromApi(id) {
    const path = this.endpointsService.allUnapprovedChallengesURL(id);
    const SELF = this;
    SELF.apiService.getUrl(path, true, false).subscribe(
      (data) => {
        const datas = data['results'];
        if (datas) {
          datas.forEach((challenge) => {
            if (challenge['approved_by_admin'] === false) {
              SELF.unapprovedChallengeList.push(challenge);
            }
          });
        }
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );
  }
}
