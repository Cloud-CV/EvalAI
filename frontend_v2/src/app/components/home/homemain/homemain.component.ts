import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-homemain',
  templateUrl: './homemain.component.html',
  styleUrls: ['./homemain.component.scss'],
})
export class HomemainComponent implements OnInit {
  /**
   * Is user logged in
   */
  isLoggedIn = false;

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param authService  AuthService Injection.
   */
  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private apiService: ApiService,
    private globalService: GlobalService,
    private authService: AuthService
  ) {}

  /**
   * Component on initialized
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
  }
}
