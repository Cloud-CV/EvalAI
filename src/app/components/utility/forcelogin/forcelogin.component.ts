import { Component, OnInit, Input } from '@angular/core';
import { GlobalService } from '../../../services/global.service';
import { Router} from '@angular/router';

/**
 * Component Class
 */
@Component({
  selector: 'app-forcelogin',
  templateUrl: './forcelogin.component.html',
  styleUrls: ['./forcelogin.component.scss']
})
export class ForceloginComponent implements OnInit {

  /**
   * Path of redirect-to page
   */
  @Input() path: string;

  /**
   * Constructor.
   * @param router  GlobalService Injection.
   * @param globalService  GlobalService Injection.
   */
  constructor(private globalService: GlobalService, private router: Router) { }

  /**
   * Component on initialized.
   */
  ngOnInit() {
  }

  /**
   * Redirects to login page.
   */
  redirectToLogin() {
    this.globalService.storeData('redirect', {path: this.path});
    this.router.navigate(['/auth/login']);
  }

}
