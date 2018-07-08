import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { GlobalService } from '../global.service';
import { AuthService } from '../services/auth.service';
import { ApiService } from '../services/api.service';
import { AboutComponent } from './about.component';
import { HeaderStaticComponent } from '../partials/nav/header-static/header-static.component';
import { FooterComponent } from '../footer/footer.component';
import { ActivatedRoute, Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientModule } from '@angular/common/http';

describe('AboutComponent', () => {
  let component: AboutComponent;
  let fixture: ComponentFixture<AboutComponent>;
  const fakeActivatedRoute = {
    snapshot: { data: {} }
  } as ActivatedRoute;
  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AboutComponent, HeaderStaticComponent, FooterComponent ],
      providers: [
      GlobalService,
      {provide: ActivatedRoute, useValue: fakeActivatedRoute},
      {provide: Router, useClass: class { navigate = jasmine.createSpy('navigate'); }},
      AuthService,
      ApiService
      ],
      imports: [ RouterTestingModule, HttpClientModule ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AboutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
