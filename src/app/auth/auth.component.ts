import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { GlobalService } from '../global.service';

@Component({
  selector: 'app-auth',
  templateUrl: './auth.component.html',
  styleUrls: ['./auth.component.scss']
})
export class AuthComponent implements OnInit {
  localRouter: any;
  constructor(private router: Router, private route: ActivatedRoute, private globalService: GlobalService) { }

  ngOnInit() {
    this.localRouter = this.router;
    this.globalService.scrollToTop();
  }
  navigateTo(url) {
    this.router.navigate([ url ]);
  }

}
