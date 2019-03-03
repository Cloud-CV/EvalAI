import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { GlobalService } from '../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-auth',
  templateUrl: './auth.component.html',
  styleUrls: ['./auth.component.scss']
})
export class AuthComponent implements OnInit {

  /**
   * router local instance
   */
  localRouter: any;

  /**
   * Constructor.
   * @param router  Router Injection.
   * @param route  ActivatedRoute Injection.
   * @param globalService  GlobalService Injection.
   */
  constructor(private router: Router, private route: ActivatedRoute, private globalService: GlobalService) { }

  /**
   * Component on initialization.
   */
  ngOnInit() {
    this.localRouter = this.router;
    this.globalService.scrollToTop();
  }

  /**
   * Navigate to a certain URL.
   * @param url  URL to navigate to (not in paranthesis)
   */
  navigateTo(url) {
    this.router.navigate([ url ]);
  }
}
