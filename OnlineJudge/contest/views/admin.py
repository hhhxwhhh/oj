import copy
import os
import zipfile
from ipaddress import ip_network
from collections import defaultdict

import dateutil.parser
from django.http import FileResponse
from django.db.models import Count, Sum, Q

from account.decorators import check_contest_permission, ensure_created_by
from account.models import User
from submission.models import Submission, JudgeStatus
from utils.api import APIView, validate_serializer
from utils.cache import cache
from utils.constants import CacheKey
from utils.shortcuts import rand_str
from utils.tasks import delete_files
from ..models import Contest, ContestAnnouncement, ACMContestRank, OIContestRank
from ..serializers import (ContestAnnouncementSerializer, ContestAdminSerializer,
                           CreateConetestSeriaizer, CreateContestAnnouncementSerializer,
                           EditConetestSeriaizer, EditContestAnnouncementSerializer,
                           ACMContesHelperSerializer, )


class ContestAPI(APIView):
    @validate_serializer(CreateConetestSeriaizer)
    def post(self, request):
        data = request.data
        data["start_time"] = dateutil.parser.parse(data["start_time"])
        data["end_time"] = dateutil.parser.parse(data["end_time"])
        data["created_by"] = request.user
        if data["end_time"] <= data["start_time"]:
            return self.error("Start time must occur earlier than end time")
        if data.get("password") and data["password"] == "":
            data["password"] = None
        for ip_range in data["allowed_ip_ranges"]:
            try:
                ip_network(ip_range, strict=False)
            except ValueError:
                return self.error(f"{ip_range} is not a valid cidr network")
        contest = Contest.objects.create(**data)
        return self.success(ContestAdminSerializer(contest).data)

    @validate_serializer(EditConetestSeriaizer)
    def put(self, request):
        data = request.data
        try:
            contest = Contest.objects.get(id=data.pop("id"))
            ensure_created_by(contest, request.user)
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")
        data["start_time"] = dateutil.parser.parse(data["start_time"])
        data["end_time"] = dateutil.parser.parse(data["end_time"])
        if data["end_time"] <= data["start_time"]:
            return self.error("Start time must occur earlier than end time")
        if not data["password"]:
            data["password"] = None
        for ip_range in data["allowed_ip_ranges"]:
            try:
                ip_network(ip_range, strict=False)
            except ValueError:
                return self.error(f"{ip_range} is not a valid cidr network")
        for k, v in data.items():
            setattr(contest, k, v)
        contest.save()
        return self.success(ContestAdminSerializer(contest).data)

    def get(self, request):
        contest_id = request.GET.get("id")
        if contest_id:
            try:
                contest = Contest.objects.get(id=contest_id)
                ensure_created_by(contest, request.user)
                return self.success(ContestAdminSerializer(contest).data)
            except Contest.DoesNotExist:
                return self.error("Contest does not exist")

        contests = Contest.objects.all().order_by("-create_time")
        if request.GET.get("keyword"):
            contests = contests.filter(title__contains=request.GET["keyword"])
        return self.success(self.paginate_data(request, contests, ContestAdminSerializer))


class ContestAnnouncementAPI(APIView):
    @validate_serializer(CreateContestAnnouncementSerializer)
    def post(self, request):
        data = request.data
        try:
            contest = Contest.objects.get(id=data.pop("contest_id"))
            ensure_created_by(contest, request.user)
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")
        data["contest"] = contest
        data["created_by"] = request.user
        announcement = ContestAnnouncement.objects.create(**data)
        return self.success(ContestAnnouncementSerializer(announcement).data)

    @validate_serializer(EditContestAnnouncementSerializer)
    def put(self, request):
        data = request.data
        try:
            contest_announcement = ContestAnnouncement.objects.get(id=data.pop("id"))
            ensure_created_by(contest_announcement, request.user)
        except ContestAnnouncement.DoesNotExist:
            return self.error("Announcement does not exist")
        try:
            contest = Contest.objects.get(id=data.pop("contest_id"))
            ensure_created_by(contest, request.user)
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")
        for k, v in data.items():
            setattr(contest_announcement, k, v)
        contest_announcement.save()
        return self.success(ContestAnnouncementSerializer(contest_announcement).data)

    def get(self, request):
        contest_announcement_id = request.GET.get("id")
        if contest_announcement_id:
            try:
                contest_announcement = ContestAnnouncement.objects.get(id=contest_announcement_id)
                ensure_created_by(contest_announcement, request.user)
                return self.success(ContestAnnouncementSerializer(contest_announcement).data)
            except ContestAnnouncement.DoesNotExist:
                return self.error("Announcement does not exist")

        contest_id = request.GET.get("contest_id")
        if not contest_id:
            return self.error("Parameter error")
        announcements = ContestAnnouncement.objects.filter(contest_id=contest_id)
        return self.success(self.paginate_data(request, announcements, ContestAnnouncementSerializer))


class ACMContestHelper(APIView):
    @check_contest_permission
    def get(self, request):
        contest_id = request.GET.get("contest_id")
        acm_rank = ACMContestRank.objects.filter(contest_id=contest_id, accepted_number__gt=0) \
            .values("user__username", "user__userprofile__real_name", "submission_number", "accepted_number",
                    "total_time") \
            .order_by("-accepted_number", "total_time")
        result = []
        for rank in acm_rank:
            result.append({
                "username": rank["user__username"],
                "real_name": rank["user__userprofile__real_name"] or "",
                "submission_number": rank["submission_number"],
                "accepted_number": rank["accepted_number"],
                "total_time": rank["total_time"]
            })
        return self.success(result)


class DownloadContestSubmissions(APIView):
    def get(self, request):
        contest_id = request.GET.get("contest_id")
        if not contest_id:
            return self.error("Parameter error")
        try:
            contest = Contest.objects.get(id=contest_id)
            ensure_created_by(contest, request.user)
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")

        exclude_admin = request.GET.get("exclude_admin") == "1"
        submissions = Submission.objects.filter(contest=contest, result=JudgeStatus.ACCEPTED)

        # Filter out admin submissions
        if exclude_admin:
            submissions = submissions.exclude(user__admin_type__in=[User.SUPER_ADMIN, User.ADMIN])

        if not submissions:
            return self.error("Submissions does not exist")

        zip_path = f"/tmp/{rand_str()}.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            for submission in submissions:
                user = submission.user
                problem = submission.problem
                filename = f"{user.username}_{problem.title}_{submission.create_time.strftime('%Y-%m-%d_%H-%M-%S')}.txt"
                zip_file.writestr(filename, submission.code)

        delete_files.apply_async((zip_path,), countdown=300)
        return FileResponse(open(zip_path, "rb"), content_type="application/zip",
                            as_attachment=True, filename=f"{contest.title}_submissions.zip")


class ContestAnalyticsAPI(APIView):
    """
    竞赛数据分析API
    """
    def get(self, request):
        contest_id = request.GET.get("contest_id")
        if not contest_id:
            return self.error("Parameter error")
        
        try:
            contest = Contest.objects.get(id=contest_id)
            ensure_created_by(contest, request.user)
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")
        if contest.rule_type == "ACM":
            participants_count = ACMContestRank.objects.filter(contest=contest).count()
        else:  # OI
            participants_count = OIContestRank.objects.filter(contest=contest).count()
        
        # 获取竞赛基本信息
        contest_info = {
            "id": contest.id,
            "title": contest.title,
            "start_time": contest.start_time,
            "end_time": contest.end_time,
            "status": contest.status,
            "rule_type": contest.rule_type,
            "participants_count": participants_count
        }
        
        # 获取提交统计数据
        submissions = Submission.objects.filter(contest_id=contest_id)
        total_submissions = submissions.count()
        accepted_submissions = submissions.filter(result=JudgeStatus.ACCEPTED).count()
        
        submission_stats = {
            "total": total_submissions,
            "accepted": accepted_submissions,
            "acceptance_rate": round(accepted_submissions / total_submissions * 100, 2) if total_submissions > 0 else 0
        }
        
        # 获取用户排名数据
        if contest.rule_type == "ACM":
            ranks = ACMContestRank.objects.filter(contest_id=contest_id) \
                .select_related('user', 'user__userprofile') \
                .order_by('-accepted_number', 'total_time')
        else:  # OI
            ranks = OIContestRank.objects.filter(contest_id=contest_id) \
                .select_related('user', 'user__userprofile') \
                .order_by('-total_score')
        
        # 构建排名数据
        rank_data = []
        for i, rank in enumerate(ranks, 1):
            user = rank.user
            profile = user.userprofile
            rank_info = {
                "rank": i,
                "username": user.username,
                "real_name": profile.real_name or "",
                "avatar": profile.avatar or "",
                "submission_number": rank.submission_number,
            }
            
            if contest.rule_type == "ACM":
                rank_info.update({
                    "accepted_number": rank.accepted_number,
                    "total_time": rank.total_time,
                })
            else:  # OI
                rank_info.update({
                    "total_score": rank.total_score,
                })
            
            rank_data.append(rank_info)
        
        # 获取题目统计数据
        problem_stats = []
        problems = contest.problem_set.all()
        for problem in problems:
            problem_submissions = submissions.filter(problem=problem)
            problem_accepted = problem_submissions.filter(result=JudgeStatus.ACCEPTED).count()
            problem_total = problem_submissions.count()
            
            problem_stats.append({
                "problem_id": problem.id,
                "problem_title": problem.title,
                "total_submissions": problem_total,
                "accepted_submissions": problem_accepted,
                "acceptance_rate": round(problem_accepted / problem_total * 100, 2) if problem_total > 0 else 0
            })
        
        # 构建时间序列数据（每小时提交数）
        import datetime
        from django.utils import timezone
        time_series_data = []
        if total_submissions > 0:
            # 获取时间范围
            start_time = timezone.localtime(contest.start_time)
            end_time = min(timezone.localtime(contest.end_time), timezone.now())
            
            # 按小时统计
            current_time = start_time.replace(minute=0, second=0, microsecond=0)
            while current_time <= end_time:
                next_hour = current_time + datetime.timedelta(hours=1)
                count = submissions.filter(
                    create_time__gte=current_time,
                    create_time__lt=next_hour
                ).count()
                
                time_series_data.append({
                    "time": current_time.strftime("%Y-%m-%d %H:%M"),
                    "count": count
                })
                
                current_time = next_hour
        
        # 构建分数分布数据
        score_distribution = []
        if contest.rule_type == "OI" and ranks.exists():
            # 对OI竞赛计算分数分布
            scores = list(ranks.values_list('total_score', flat=True))
            if scores:
                min_score = min(scores)
                max_score = max(scores)
                range_size = (max_score - min_score) / 10 or 1  # 防止除零
                
                for i in range(10):
                    range_min = min_score + i * range_size
                    range_max = min_score + (i + 1) * range_size
                    
                    count = sum(1 for score in scores if range_min <= score < range_max)
                    # 最后一个区间包含最大值
                    if i == 9:
                        count = sum(1 for score in scores if range_min <= score <= range_max)
                    
                    score_distribution.append({
                        "range": f"{int(range_min)}-{int(range_max)}",
                        "count": count
                    })
        
        analytics_data = {
            "contest_info": contest_info,
            "submission_stats": submission_stats,
            "rank_data": rank_data[:20],  # 只返回前20名
            "problem_stats": problem_stats,
            "time_series_data": time_series_data[-24:],  # 只返回最近24小时的数据
            "score_distribution": score_distribution
        }
        
        return self.success(analytics_data)