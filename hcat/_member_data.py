from .models import Member, Branch, MemberStatus


# YouTube handles are case-insensitive; we store lowercase for matching
INITIAL_MEMBERS = [
    # ── EN ─────────────────────────────────────────────
    Member("moricalliope", "Mori Calliope", branch=Branch.EN),
    Member("takanashikiara", "Takanashi Kiara", branch=Branch.EN),
    Member("ninomaeinanis", "Ninomae Ina'nis", branch=Branch.EN),
    Member("irys", "IRyS", branch=Branch.EN),
    Member("ourokronii", "Ouro Kronii", branch=Branch.EN),
    Member("hakosbaelz", "Hakos Baelz", branch=Branch.EN),
    Member("nanashimumei", "Nanashi Mumei", branch=Branch.EN),

    # Advent
    Member("shiorinovella", "Shiori Novella", branch=Branch.EN),
    Member("kosekibijou", "Koseki Bijou", branch=Branch.EN),
    Member("nerissa_ravencroft", "Nerissa Ravencroft", branch=Branch.EN),
    Member("fuwa_amano", "Fuwa Amano", branch=Branch.EN),
    Member("mococo_abyssgard", "Mococo Abyssgard", branch=Branch.EN),

    # Justice
    Member("elizabethrosebloodflame", "Elizabeth Rose Bloodflame", branch=Branch.EN),
    Member("gigi_murin", "Gigi Murin", branch=Branch.EN),
    Member("cecilia_immergreen", "Cecilia Immergreen", branch=Branch.EN),
    Member("raorapanthera", "Raora Panthera", branch=Branch.EN),

    # EN (graduated)
    Member("gawrgura", "Gawr Gura", branch=Branch.EN, status=MemberStatus.GRADUATED, graduated_at="2025-06-30"),
    Member("watsonamelia", "Watson Amelia", branch=Branch.EN, status=MemberStatus.GRADUATED, graduated_at="2025-10-01"),
    Member("ceresfauna", "Ceres Fauna", branch=Branch.EN, status=MemberStatus.GRADUATED, graduated_at="2025-03-31"),
    Member("tsukumosana", "Tsukumo Sana", branch=Branch.EN, status=MemberStatus.GRADUATED, graduated_at="2023-06-30"),

    # ── Official ────────────────────────────────────────
    Member("hololive", "ホロライブ公式", branch=Branch.OFFICIAL),
    Member("hololiveenglish", "hololive English", branch=Branch.OFFICIAL),
    Member("hololiveindonesia", "hololive Indonesia", branch=Branch.OFFICIAL),
    Member("hololive_music", "hololive Music", branch=Branch.OFFICIAL),

    # ── ID ────────────────────────────────────────────
    Member("ayunda_risu", "Ayunda Risu", branch=Branch.ID),
    Member("moona_hoshinova", "Moona Hoshinova", branch=Branch.ID),
    Member("airaniiofifteen", "Airani Iofifteen", branch=Branch.ID),
    Member("kureijiollie", "Kureiji Ollie", branch=Branch.ID),
    Member("aniamelfissa", "Anya Melfissa", branch=Branch.ID),
    Member("pavoliareine", "Pavolia Reine", branch=Branch.ID),
    Member("vestia_zeta", "Vestia Zeta", branch=Branch.ID),
    Member("kaelakovalskia", "Kaela Kovalskia", branch=Branch.ID),
    Member("kobokanaeru", "Kobo Kanaeru", branch=Branch.ID),

    # ── JP (Gen 0+1+2+Gamers) ─────────────────────────
    Member("tokinosora", "Tokino Sora", branch=Branch.JP),
    Member("robocosan", "Robocosan", branch=Branch.JP),
    Member("sakuramiko", "Sakura Miko", branch=Branch.JP),
    Member("akirose", "Aki Rosenthal", branch=Branch.JP),
    Member("akaihaato", "Akai Haato", branch=Branch.JP),
    Member("shirakamifubuki", "Shirakami Fubuki", branch=Branch.JP),
    Member("nekomataokayu", "Nekomata Okayu", branch=Branch.JP),
    Member("inugamikorone", "Inugami Korone", branch=Branch.JP),
    Member("ookamimio", "Ookami Mio", branch=Branch.JP),
    Member("natsuiromatsuri", "Natsuiro Matsuri", branch=Branch.JP),

    # ── JP (3rd Gen) ─────────────────────────────────
    Member("usadapekora", "Usada Pekora", branch=Branch.JP),
    Member("shiranuiflare", "Shiranui Flare", branch=Branch.JP),
    Member("shiroganenoel", "Shirogane Noel", branch=Branch.JP),
    Member("houshoumarine", "Houshou Marine", branch=Branch.JP),

    # ── JP (4th Gen) ─────────────────────────────────
    Member("amanekanata", "Amane Kanata", branch=Branch.JP),
    Member("tsunomakiwatame", "Tsunomaki Watame", branch=Branch.JP),
    Member("tokoyamitowa", "Tokoyami Towa", branch=Branch.JP),
    Member("himemoriluna", "Himemori Luna", branch=Branch.JP),

    # ── JP (5th Gen) ─────────────────────────────────
    Member("yukihanalamy", "Yukihana Lamy", branch=Branch.JP),
    Member("momosuzunene", "Momosuzu Nene", branch=Branch.JP),
    Member("shishirobotan", "Shishiro Botan", branch=Branch.JP),
    Member("omarupolka", "Omaru Polka", branch=Branch.JP),

    # ── JP (HoloX - 6th Gen) ─────────────────────────
    Member("ladarknesss", "La+ Darknesss", branch=Branch.JP),
    Member("takanelui", "Takane Lui", branch=Branch.JP),
    Member("hakuikoyori", "Hakui Koyori", branch=Branch.JP),
    Member("sakamatachloe", "Sakamata Chloe", branch=Branch.JP),
    Member("kazamairoha", "Kazama Iroha", branch=Branch.JP),

    # ── DEV_IS / ReGLOSS ────────────────────────────
    Member("otonosekanade", "Otonose Kanade", branch=Branch.DEV_IS),
    Member("ichijouririka", "Ichijou Ririka", branch=Branch.DEV_IS),
    Member("juufuuteiraden", "Juufuutei Raden", branch=Branch.DEV_IS),
    Member("todorokihajime", "Todoroki Hajime", branch=Branch.DEV_IS),

    # ── DEV_IS / FLOW GLOW ──────────────────────────
    Member("isakiriona", "Isaki Riona", branch=Branch.DEV_IS),
    Member("koganei_niko", "Koganei Niko", branch=Branch.DEV_IS),
    Member("mizumiya_su", "Mizumiya Su", branch=Branch.DEV_IS),
    Member("rindo_chihaya", "Rindo Chihaya", branch=Branch.DEV_IS),
    Member("kikirara_vivi", "Kikirara Vivi", branch=Branch.DEV_IS),

    # ── DEV_IS (graduated) ──────────────────────────
    Member("hiodoshi_ao", "Hiodoshi Ao", branch=Branch.DEV_IS, status=MemberStatus.GRADUATED, graduated_at="2025-04-01"),

    # ── holoAN (공식 아나운서, 개인 채널 없음) ──────
    Member("izuki_michiru", "Izuki Michiru", branch=Branch.HOLOAN),
    Member("hanazono_sayaka", "Hanazono Sayaka", branch=Branch.HOLOAN),
    Member("kazeshiro_yuki", "Kazeshiro Yuki", branch=Branch.HOLOAN),
    Member("harusaki_nodoka", "Harusaki Nodoka", branch=Branch.HOLOAN, status=MemberStatus.GRADUATED, graduated_at="2025-09-30"),

    # ── JP (graduated/terminated) ─────────────────────
    Member("kiryucoco", "Kiryu Coco", branch=Branch.JP, status=MemberStatus.GRADUATED, graduated_at="2021-07-01"),
    Member("uruharushia", "Uruha Rushia", branch=Branch.JP, status=MemberStatus.TERMINATED, graduated_at="2022-02-24"),
    Member("yozoramel", "Yozora Mel", branch=Branch.JP, status=MemberStatus.GRADUATED, graduated_at="2024-01-16"),
    Member("murasakishion", "Murasaki Shion", branch=Branch.JP, status=MemberStatus.GRADUATED, graduated_at="2025-04-01"),

    # ── Holostars ─────────────────────────────────────
    Member("arurandeisu", "Arurandeisu", branch=Branch.HOLOSTARS),
    Member("rikka_riki", "Rikka", branch=Branch.HOLOSTARS),
    Member("astelleda", "Astel Leda", branch=Branch.HOLOSTARS),
    Member("kishidotemma", "Kishido Temma", branch=Branch.HOLOSTARS),
    Member("yukokuroberu", "Yukoku Roberu", branch=Branch.HOLOSTARS),
    Member("kageyamashien", "Kageyama Shien", branch=Branch.HOLOSTARS),
]
