import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { GlobalService } from '../../services/global.service';
import { AuthService } from '../../services/auth.service';
import { EndpointsService } from '../../services/endpoints.service';
import { ApiService } from '../../services/api.service';
import { AboutComponent } from './about.component';
import { HeaderStaticComponent } from '../../components/nav/header-static/header-static.component';
import { FooterComponent } from '../../components/nav/footer/footer.component';
import { ActivatedRoute, Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientModule } from '@angular/common/http';

describe('AboutComponent', () => {
  let component: AboutComponent;
  let fixture: ComponentFixture<AboutComponent>;
  const fakeActivatedRoute = {
    snapshot: { data: {} },
  } as ActivatedRoute;
  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [AboutComponent, HeaderStaticComponent, FooterComponent],
      providers: [GlobalService, AuthService, ApiService, EndpointsService],
      imports: [RouterTestingModule, HttpClientModule],
    }).compileComponents();
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
