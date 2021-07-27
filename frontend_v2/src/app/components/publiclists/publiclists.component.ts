import { Component, OnInit, Inject, OnDestroy, AfterViewChecked, ChangeDetectorRef } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { DOCUMENT } from '@angular/common';
import { GlobalService } from '../../services/global.service';
import { AuthService } from '../../services/auth.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-publiclists',
  templateUrl: './publiclists.component.html',
  styleUrls: ['./publiclists.component.scss'],
})
export class PubliclistsComponent implements OnInit, AfterViewChecked {

  isAuth = false;

  /**
   * Constructor.
   * @param document  Window document Injection.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param authService
   * @param globalService  GlobalService Injection.
   */
  constructor(
    private router: Router,
    private route: ActivatedRoute,
    @Inject(DOCUMENT) private document: Document,
    public authService: AuthService,
    private globalService: GlobalService,
    private cdRef : ChangeDetectorRef
  ) {}
  
  /**
   * Component on Initialization.
   */
  ngOnInit() {
    this.isAuth = this.authService.isAuth;
  }
  /**
   * DEV MODE:
   * For resolving change in expression value after it is checked
   */

  ngAfterViewChecked() {
    let isAuth = this.authService.isAuth;
    if(isAuth != this.isAuth) {
      this.isAuth = isAuth;
      this.cdRef.detectChanges();
    }
  }
}
