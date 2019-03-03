import { Component, OnInit, Inject } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { DOCUMENT } from '@angular/common';
import { GlobalService } from '../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-publiclists',
  templateUrl: './publiclists.component.html',
  styleUrls: ['./publiclists.component.scss']
})
export class PubliclistsComponent implements OnInit {

  /**
   * Router local/public instance
   */
  localRouter: any;

  /**
   * Constructor.
   * @param document  Window document Injection.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   */
  constructor(private router: Router, private route: ActivatedRoute, @Inject(DOCUMENT) private document: Document,
              private globalService: GlobalService) { }

  /**
   * Component on intialized.
   */
  ngOnInit() {
    this.localRouter = this.router;
    this.scrollNav();
    this.globalService.scrollToTop();
  }

  /**
   * Scroll Navigation headers on challenges and team pages.
   */
  scrollNav() {
    if (this.router.url === '/challenges/all') {
      this.document.getElementById('all-challenges-nav').scrollIntoView();
    } else if (this.router.url === '/challenges/me') {
      this.document.getElementById('all-challenges-nav').scrollIntoView();
    } else if (this.router.url === '/teams/participants') {
      this.document.getElementById('host-teams-nav').scrollIntoView();
    } else if (this.router.url === '/teams/hosts') {
      this.document.getElementById('host-teams-nav').scrollIntoView();
    }
  }
}
